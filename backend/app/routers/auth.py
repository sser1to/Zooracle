from datetime import timedelta, datetime
import logging
import os
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, PasswordResetToken
from ..schemas import (
    UserCreate, 
    Token, 
    UserResponse, 
    UserLogin, 
    PasswordResetRequest, 
    PasswordReset, 
    EmailVerificationRequest,
    EmailVerificationCode
)
from ..services.auth_service import (
    authenticate_user, 
    create_access_token, 
    get_password_hash, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..services.email_verification_service import (
    create_verification_code,
    verify_code
)
from ..services.user_registration_service import (
    store_pending_user,
    get_pending_user,
    remove_pending_user
)
from ..services.smtp_service import send_email_verification_code

# Настройка логирования
logger = logging.getLogger("auth_router")

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя в системе.
    
    Args:
        user_data (UserCreate): Данные нового пользователя (логин, email, пароль)
        db (Session): Сессия базы данных
        
    Returns:
        dict: Информация об успешной отправке кода верификации
        
    Raises:
        HTTPException: 400 - если пользователь с таким логином или email уже существует
    """
    try:
        # Логирование начала операции
        logger.info(f"Попытка регистрации пользователя с логином: {user_data.login} и email: {user_data.email}")
        
        # Проверка, существует ли пользователь с таким логином
        db_user = db.query(User).filter(User.login == user_data.login).first()
        if db_user:
            logger.warning(f"Ошибка: пользователь с логином {user_data.login} уже существует")
            raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
        
        # Проверка, существует ли пользователь с таким email
        db_user = db.query(User).filter(User.email == user_data.email).first()
        if db_user:
            logger.warning(f"Ошибка: пользователь с email {user_data.email} уже существует")
            raise HTTPException(status_code=400, detail="Пользователь с такой почтой уже существует")
        
        # Валидация пароля
        if len(user_data.password) < 6:
            logger.warning("Ошибка: пароль слишком короткий")
            raise HTTPException(status_code=400, detail="Пароль должен быть не менее 6 символов")

        # Валидация email формата
        if "@" not in user_data.email or "." not in user_data.email:
            logger.warning(f"Ошибка: некорректный формат email: {user_data.email}")
            raise HTTPException(status_code=400, detail="Некорректный формат email")
            
        # Хеширование пароля
        logger.info("Хеширование пароля...")
        try:
            hashed_password = get_password_hash(user_data.password)
        except Exception as e:
            logger.error(f"Ошибка при хешировании пароля: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Ошибка при обработке пароля: {str(e)}")
        
        # Сохраняем данные пользователя во временном хранилище
        pending_user_data = {
            "login": user_data.login,
            "email": user_data.email,
            "password": hashed_password,
            "is_admin": False
        }
        
        # Сохраняем данные во временное хранилище
        logger.info(f"Сохранение данных пользователя {user_data.login} во временное хранилище")
        store_pending_user(user_data.email, pending_user_data)
        
        # Генерируем код верификации для email
        verification_code = create_verification_code(user_data.email)
        
        # Отправляем код на email пользователя
        email_sent = send_email_verification_code(user_data.email, verification_code)
        
        if not email_sent:
            logger.warning(f"Не удалось отправить код верификации на {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось отправить код подтверждения. Пожалуйста, попробуйте позже."
            )
        
        logger.info(f"Данные пользователя {user_data.login} сохранены для верификации email")
        return {
            "message": "На указанный email отправлен код подтверждения",
            "email": user_data.email
        }
            
    except HTTPException:
        # Пробрасываем HTTPException дальше
        raise
    except Exception as e:
        # Логируем и обрабатываем все остальные исключения
        logger.error(f"Непредвиденная ошибка при регистрации пользователя: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка при регистрации пользователя: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.login}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "login": user.login,
        "email": user.email,
        "is_admin": user.is_admin
    }


@router.post("/verify-email/request")
async def request_email_verification(verification_data: EmailVerificationRequest):
    """
    Запрашивает отправку кода верификации email.
    
    Args:
        verification_data (EmailVerificationRequest): Email для верификации
    
    Returns:
        dict: Сообщение о результате операции
    """
    logger.info(f"Запрос на верификацию email: {verification_data.email}")
    
    # Проверяем наличие временных данных для этого email
    pending_user = get_pending_user(verification_data.email)
    
    # Для безопасности не раскрываем, существуют ли такие данные
    if not pending_user:
        logger.warning(f"Запрос верификации для несуществующего email в ожидающих регистрацию: {verification_data.email}")
        return {"message": "Если указанный email существует и не подтвержден, код подтверждения был отправлен"}
    
    # Генерируем новый код верификации
    verification_code = create_verification_code(verification_data.email)
    
    # Отправляем код на указанный email
    email_sent = send_email_verification_code(verification_data.email, verification_code)
    
    if email_sent:
        logger.info(f"Код верификации успешно отправлен на {verification_data.email}")
        return {"message": "Код подтверждения отправлен на указанный email"}
    else:
        logger.error(f"Не удалось отправить код верификации на {verification_data.email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось отправить код подтверждения. Пожалуйста, попробуйте позже."
        )


@router.post("/verify-email/confirm", response_model=Token)
async def confirm_email(verification_data: EmailVerificationCode, db: Session = Depends(get_db)):
    """
    Подтверждает email с помощью кода верификации и создает пользователя в базе данных.
    
    Args:
        verification_data (EmailVerificationCode): Email и код верификации
        db (Session): Сессия базы данных
    
    Returns:
        Token: Токен доступа для авторизации
    """
    logger.info(f"Попытка подтверждения email: {verification_data.email}")
    
    # Проверяем корректность кода верификации
    is_verified = verify_code(verification_data.email, verification_data.code)
    
    if not is_verified:
        logger.warning(f"Неверный код верификации для {verification_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный код подтверждения"
        )
    
    # Получаем временные данные пользователя
    pending_user = get_pending_user(verification_data.email)
    if not pending_user:
        logger.warning(f"Временные данные пользователя не найдены для {verification_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Данные для регистрации не найдены или срок действия истек. Пройдите регистрацию повторно."
        )
    
    # Создаем пользователя в базе данных
    try:
        # Создаем объект пользователя
        db_user = User(
            login=pending_user["login"],
            email=pending_user["email"],
            password=pending_user["password"],
            is_admin=pending_user["is_admin"]
        )
        
        logger.info(f"Создание пользователя в БД: {pending_user['login']}")
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Удаляем временные данные
        remove_pending_user(verification_data.email)
        
        # Генерируем токен доступа для автоматического входа
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user.login}, expires_delta=access_token_expires
        )
        
        logger.info(f"Пользователь {db_user.login} успешно создан после подтверждения email")
        
        # Возвращаем токен доступа для автоматического входа
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": db_user.id,
            "login": db_user.login,
            "email": db_user.email,
            "is_admin": db_user.is_admin
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при создании пользователя: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании пользователя: {str(e)}"
        )