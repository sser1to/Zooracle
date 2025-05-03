from datetime import timedelta, datetime
import logging
import os
from fastapi import APIRouter, Depends, HTTPException, status, Request, Security
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
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
    EmailVerificationCode,
    TokenData
)
from ..services.auth_service import (
    authenticate_user, 
    create_access_token, 
    get_password_hash, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM
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
from ..services.smtp_service import send_email_verification_code, send_password_reset_email

# Настройка логирования
logger = logging.getLogger("auth_router")

# Создаем экземпляр OAuth2PasswordBearer для получения токена из запроса
# Обратите внимание на исправленный URL для tokenUrl, он должен соответствовать
# фактическому пути к эндпоинту login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

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


@router.post("/reset-password/request", status_code=status.HTTP_200_OK)
def request_password_reset(reset_request: PasswordResetRequest, db: Session = Depends(get_db), request: Request = None):
    """
    Обрабатывает запрос на восстановление пароля
    
    Args:
        reset_request (PasswordResetRequest): Данные запроса (email пользователя)
        db (Session): Сессия базы данных
        request (Request): Данные HTTP запроса для формирования URL сброса пароля
        
    Returns:
        dict: Сообщение об успешной отправке инструкций
        
    Raises:
        HTTPException: Если произошла ошибка при обработке запроса
    """
    logger.info(f"Запрос на сброс пароля для email: {reset_request.email}")
    
    try:
        # Проверяем, есть ли пользователь с таким email
        user = db.query(User).filter(User.email == reset_request.email).first()
        
        # Для безопасности не сообщаем, существует ли такой пользователь
        if not user:
            logger.warning(f"Запрос сброса пароля для несуществующего пользователя: {reset_request.email}")
            # Возвращаем успешный ответ, чтобы не раскрывать информацию о существовании пользователя
            return {"message": "Если указанный email зарегистрирован, инструкции по сбросу пароля были отправлены."}
        
        # Проверяем, есть ли активные токены для этого пользователя, и инвалидируем их
        existing_tokens = db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        ).all()
        
        for token in existing_tokens:
            token.is_used = True
            logger.info(f"Инвалидация существующего токена для пользователя {user.id}")
        
        # Создаем новый токен для сброса пароля
        reset_token = PasswordResetToken.generate(user.id, user.email)
        
        # Сохраняем токен в базе данных
        db.add(reset_token)
        db.commit()
        
        # Формируем URL для сброса пароля
        frontend_url = os.getenv("FRONTEND_URL")
        reset_url = f"{frontend_url}/reset-password-confirm?token={reset_token.token}"
        
        # Отправляем письмо с инструкциями по сбросу пароля
        email_sent = send_password_reset_email(user.email, reset_url)
        
        if not email_sent:
            logger.error(f"Не удалось отправить письмо для сброса пароля на {user.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось отправить инструкции по сбросу пароля. Пожалуйста, попробуйте позже."
            )
        
        logger.info(f"Инструкции по сбросу пароля успешно отправлены на {user.email}")
        return {"message": "Инструкции по сбросу пароля отправлены на указанный email."}
    
    except HTTPException:
        # Пробрасываем HTTPException дальше
        raise
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса на сброс пароля: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже."
        )


@router.post("/reset-password/confirm", status_code=status.HTTP_200_OK)
def confirm_password_reset(reset_data: PasswordReset, db: Session = Depends(get_db)):
    """
    Подтверждает сброс пароля с использованием токена и устанавливает новый пароль
    
    Args:
        reset_data (PasswordReset): Данные для сброса пароля (токен и новый пароль)
        db (Session): Сессия базы данных
        
    Returns:
        dict: Сообщение об успешном сбросе пароля
        
    Raises:
        HTTPException: Если токен недействителен или произошла ошибка при сбросе пароля
    """
    logger.info("Запрос на подтверждение сброса пароля")
    
    try:
        # Проверяем, что пароли совпадают
        if reset_data.password != reset_data.confirm_password:
            logger.warning("Ошибка: пароли не совпадают")
            raise HTTPException(status_code=400, detail="Пароли не совпадают")
        
        # Ищем токен в базе данных
        token_record = db.query(PasswordResetToken).filter(PasswordResetToken.token == reset_data.token).first()
        
        # Проверяем, что токен существует
        if not token_record:
            logger.warning("Попытка сброса пароля с несуществующим токеном")
            raise HTTPException(status_code=400, detail="Недействительный токен для сброса пароля")
        
        # Проверяем, что токен действителен (не использован и не истек)
        if not token_record.is_valid():
            logger.warning(f"Попытка использовать недействительный токен: использован={token_record.is_used}, истек={token_record.expires_at < datetime.utcnow()}")
            raise HTTPException(status_code=400, detail="Токен для сброса пароля недействителен или истек срок его действия")
        
        # Получаем пользователя по ID из токена
        user = db.query(User).filter(User.id == token_record.user_id).first()
        
        if not user:
            logger.error(f"Пользователь с ID {token_record.user_id} не найден для токена {reset_data.token}")
            raise HTTPException(status_code=400, detail="Пользователь не найден")
        
        # Проверяем, что email пользователя совпадает с тем, что в токене
        if user.email != token_record.email:
            logger.warning(f"Email пользователя {user.email} не совпадает с email в токене {token_record.email}")
            raise HTTPException(status_code=400, detail="Недействительный токен для сброса пароля")
        
        # Хешируем новый пароль
        hashed_password = get_password_hash(reset_data.password)
        
        # Обновляем пароль пользователя
        user.password = hashed_password
        
        # Помечаем токен как использованный
        token_record.invalidate()
        
        # Сохраняем изменения в базе данных
        db.commit()
        
        logger.info(f"Пароль успешно сброшен для пользователя с ID {user.id}")
        return {"message": "Пароль успешно изменен"}
    
    except HTTPException:
        # Пробрасываем HTTPException дальше
        raise
    except Exception as e:
        logger.error(f"Ошибка при подтверждении сброса пароля: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже."
        )


@router.get("/reset-password/validate-token/{token}", status_code=status.HTTP_200_OK)
def validate_reset_token(token: str, db: Session = Depends(get_db)):
    """
    Проверяет валидность токена для сброса пароля
    
    Args:
        token (str): Токен для проверки
        db (Session): Сессия базы данных
        
    Returns:
        dict: Результат проверки токена с указанием причины невалидности
    """
    logger.info(f"Запрос на валидацию токена для сброса пароля")
    
    try:
        # Ищем токен в базе данных
        token_record = db.query(PasswordResetToken).filter(PasswordResetToken.token == token).first()
        
        # Проверяем существование токена
        if not token_record:
            logger.warning(f"Токен не найден в базе данных")
            return {
                "valid": False,
                "reason": "token_not_found"
            }
        
        # Проверка, не использован ли уже токен
        if token_record.is_used:
            logger.warning(f"Токен {token} уже был использован")
            return {
                "valid": False,
                "reason": "token_used"
            }
        
        # Проверка срока действия токена
        if datetime.utcnow() > token_record.expires_at:
            logger.warning(f"Срок действия токена {token} истек")
            return {
                "valid": False,
                "reason": "token_expired"
            }
        
        # Получение пользователя
        user = db.query(User).filter(User.id == token_record.user_id).first()
        if not user:
            logger.error(f"Пользователь с ID {token_record.user_id} не найден для токена {token}")
            return {
                "valid": False,
                "reason": "user_not_found"
            }
        
        # Проверка соответствия email
        if user.email != token_record.email:
            logger.warning(f"Email пользователя {user.email} не совпадает с email в токене {token_record.email}")
            return {
                "valid": False,
                "reason": "email_changed"
            }
        
        # Если все проверки пройдены, токен действителен
        logger.info(f"Токен {token} действителен")
        return {
            "valid": True,
            "email": token_record.email  # Можно добавить дополнительную информацию
        }
        
    except Exception as e:
        logger.error(f"Ошибка при проверке токена: {str(e)}")
        return {
            "valid": False,
            "reason": "token_invalid"
        }


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserResponse:
    """
    Получает текущего пользователя на основе JWT токена
    
    Args:
        token (str): JWT токен авторизации
        db (Session): Сессия базы данных
        
    Returns:
        UserResponse: Данные авторизованного пользователя
        
    Raises:
        HTTPException: Если токен недействителен или пользователь не найден
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Декодируем JWT токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    # Получаем пользователя из базы данных по логину
    user = db.query(User).filter(User.login == token_data.username).first()
    if user is None:
        raise credentials_exception
    
    # Возвращаем данные пользователя
    return UserResponse(
        id=user.id,
        login=user.login,
        email=user.email,
        is_admin=user.is_admin
    )


# Добавляем функцию для получения текущего администратора
# Это обертка над get_current_user, которая проверяет права администратора
async def get_current_admin(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """
    Проверяет, что текущий пользователь имеет права администратора
    
    Args:
        current_user (UserResponse): Текущий пользователь
        
    Returns:
        UserResponse: Данные администратора
        
    Raises:
        HTTPException: Если пользователь не является администратором
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора"
        )
    return current_user