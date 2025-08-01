from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import TokenData

# Секретный ключ для JWT
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080 # 7 дней

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Хеширование пароля с использованием библиотеки passlib.
    
    Args:
        password (str): Пароль в открытом виде
        
    Returns:
        str: Хешированный пароль
        
    Raises:
        ValueError: Если пароль пустой или не является строкой
    """
    try:
        # Проверяем валидность пароля
        if not password:
            raise ValueError("Пароль не может быть пустым")
        
        if not isinstance(password, str):
            raise ValueError(f"Пароль должен быть строкой, получено: {type(password)}")
        
        # Генерируем хеш пароля
        hashed = pwd_context.hash(password)
        print(f"Пароль успешно хеширован, длина хеша: {len(hashed)}")
        return hashed
        
    except Exception as e:
        print(f"Ошибка при хешировании пароля: {str(e)}")
        raise ValueError("Невозможно захешировать пароль. Проверьте формат и длину пароля.")


def authenticate_user(db: Session, username: str, password: str):
    # Поддерживаем вход по логину или email
    user = db.query(User).filter((User.login == username) | (User.email == username)).first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недействительные учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.login == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав доступа"
        )
    return current_user