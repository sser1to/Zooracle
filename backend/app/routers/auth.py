from datetime import timedelta
import logging
import os
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, Token, UserResponse, UserLogin, PasswordResetRequest, PasswordReset
from ..services.auth_service import (
    authenticate_user, 
    create_access_token, 
    get_password_hash, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..services.smtp_service import (
    generate_password_reset_token,
    send_password_reset_email,
    verify_reset_token,
    invalidate_token
)

# Настройка логирования
logger = logging.getLogger("auth_router")

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя в системе.
    
    Args:
        user_data (UserCreate): Данные нового пользователя (логин, email, пароль)
        db (Session): Сессия базы данных
        
    Returns:
        UserResponse: Информация о созданном пользователе
        
    Raises:
        HTTPException: 400 - если пользователь с таким логином или email уже существует
    """
    try:
        # Логирование начала операции
        print(f"Попытка регистрации пользователя с логином: {user_data.login} и email: {user_data.email}")
        
        # Проверка, существует ли пользователь с таким логином
        db_user = db.query(User).filter(User.login == user_data.login).first()
        if db_user:
            print(f"Ошибка: пользователь с логином {user_data.login} уже существует")
            raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
        
        # Проверка, существует ли пользователь с таким email
        db_user = db.query(User).filter(User.email == user_data.email).first()
        if db_user:
            print(f"Ошибка: пользователь с email {user_data.email} уже существует")
            raise HTTPException(status_code=400, detail="Пользователь с такой почтой уже существует")
        
        # Валидация пароля
        if len(user_data.password) < 6:
            print("Ошибка: пароль слишком короткий")
            raise HTTPException(status_code=400, detail="Пароль должен быть не менее 6 символов")

        # Валидация email формата
        if "@" not in user_data.email or "." not in user_data.email:
            print(f"Ошибка: некорректный формат email: {user_data.email}")
            raise HTTPException(status_code=400, detail="Некорректный формат email")
            
        # Создание нового пользователя
        print("Хеширование пароля...")
        try:
            hashed_password = get_password_hash(user_data.password)
        except Exception as e:
            print(f"Ошибка при хешировании пароля: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Ошибка при обработке пароля: {str(e)}")
        
        print("Создание объекта пользователя")
        try:
            db_user = User(
                login=user_data.login,
                email=user_data.email,
                password=hashed_password,
                is_admin=False  # По умолчанию пользователь не админ
            )
        except Exception as e:
            print(f"Ошибка при создании объекта пользователя: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Ошибка при создании пользователя: {str(e)}")
        
        try:
            print("Добавление пользователя в БД")
            db.add(db_user)
            
            print("Выполнение коммита...")
            db.commit()
            
            print("Обновление данных пользователя...")
            db.refresh(db_user)
            
            print(f"Пользователь {user_data.login} успешно зарегистрирован")
            return db_user
        except Exception as e:
            print(f"Ошибка при сохранении пользователя в БД: {str(e)}")
            db.rollback()  # Откатываем изменения в случае ошибки
            raise HTTPException(status_code=500, detail=f"Ошибка при сохранении пользователя: {str(e)}")
            
    except HTTPException:
        # Пробрасываем HTTPException дальше
        raise
    except Exception as e:
        # Логируем и обрабатываем все остальные исключения
        print(f"Непредвиденная ошибка при регистрации пользователя: {str(e)}")
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


@router.post("/reset-password/request")
async def request_password_reset(request: Request, reset_data: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Обработка запроса на сброс пароля.
    
    Args:
        request (Request): Объект запроса FastAPI
        reset_data (PasswordResetRequest): Email пользователя
        db (Session): Сессия базы данных
        
    Returns:
        dict: Сообщение о результате операции
    """
    # Логируем запрос
    logger.info(f"Получен запрос на восстановление пароля для email: {reset_data.email}")
    
    # Находим пользователя в базе по email
    user = db.query(User).filter(User.email == reset_data.email).first()
    
    # Даже если пользователь не найден, не сообщаем об этом для безопасности
    if not user:
        logger.warning(f"Пользователь с email {reset_data.email} не найден в базе")
        return {"message": "Если пользователь с указанным email существует, на него отправлены инструкции по сбросу пароля"}
    
    logger.info(f"Пользователь с ID={user.id} найден для email {reset_data.email}")
    
    # Генерируем токен для сброса пароля
    token = generate_password_reset_token(user.id, user.email)
    
    # Формируем URL для сброса пароля
    # Сначала пытаемся использовать FRONTEND_URL из переменных окружения
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        # Удаляем завершающий слеш, если он есть
        if frontend_url.endswith('/'):
            frontend_url = frontend_url[:-1]
        
        logger.info(f"Используем FRONTEND_URL из окружения: {frontend_url}")
        reset_url = f"{frontend_url}/reset-password/confirm?token={token}"
    else:
        # Определяем базовый URL из запроса
        base_url = str(request.base_url)
        logger.info(f"FRONTEND_URL не задан, используем базовый URL из запроса: {base_url}")
        
        # Извлекаем протокол и хост
        protocol = "http"
        host = "localhost:8080"  # Значение по умолчанию
        
        if "://" in base_url:
            protocol = base_url.split("://")[0]
            host_part = base_url.split("://")[1]
            if "/" in host_part:
                host = host_part.split("/")[0]
            else:
                host = host_part
        
        # Если мы в локальном окружении, используем localhost:8080
        if "localhost" in host or "127.0.0.1" in host:
            reset_url = f"{protocol}://localhost:8080/reset-password/confirm?token={token}"
        else:
            # Иначе используем хост из запроса
            reset_url = f"{protocol}://{host}/reset-password/confirm?token={token}"
    
    logger.info(f"Сформирован URL для сброса пароля: {reset_url}")
    
    # Отправляем email со ссылкой для сброса пароля
    logger.info(f"Отправляем письмо на {user.email} с URL: {reset_url}")
    success = send_password_reset_email(user.email, reset_url)
    
    if success:
        logger.info(f"Письмо для сброса пароля успешно отправлено на {user.email}")
        return {"message": "Инструкции по сбросу пароля отправлены на указанный email"}
    else:
        logger.error(f"Не удалось отправить письмо для сброса пароля на {user.email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось отправить email. Пожалуйста, попробуйте позже."
        )

@router.post("/reset-password/confirm")
async def confirm_password_reset(reset_data: PasswordReset, db: Session = Depends(get_db)):
    """
    Подтверждение сброса пароля и установка нового пароля.
    
    Args:
        reset_data (PasswordReset): Токен и новый пароль
        db (Session): Сессия базы данных
        
    Returns:
        dict: Сообщение о результате операции
    """
    logger.info(f"Получен запрос на подтверждение сброса пароля с токеном: {reset_data.token[:10]}...")
    
    # Проверяем совпадение паролей
    if reset_data.password != reset_data.confirm_password:
        logger.warning("Пароли не совпадают при попытке сброса пароля")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пароли не совпадают"
        )
    
    # Проверяем токен
    token_data = verify_reset_token(reset_data.token)
    if not token_data:
        logger.warning(f"Недействительный токен: {reset_data.token[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительная или истекшая ссылка для сброса пароля"
        )
    
    # Получаем пользователя по ID из токена
    user_id = token_data["user_id"]
    logger.info(f"Токен действителен для пользователя ID={user_id}")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.error(f"Пользователь с ID={user_id} не найден в БД")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Проверяем, что email не изменился
    if user.email != token_data["email"]:
        logger.warning(f"Email пользователя ({user.email}) не совпадает с email в токене ({token_data['email']})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email пользователя не совпадает с email в токене"
        )
    
    logger.info(f"Устанавливаем новый пароль для пользователя ID={user_id}")
    # Обновляем пароль пользователя
    user.password = get_password_hash(reset_data.password)
    
    try:
        # Сохраняем изменения
        db.commit()
        logger.info(f"Пароль успешно обновлен для пользователя ID={user_id}")
        
        # Инвалидируем токен после использования
        invalidate_token(reset_data.token)
        
        return {"message": "Пароль успешно изменен"}
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при изменении пароля: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при изменении пароля: {str(e)}"
        )