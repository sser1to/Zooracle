from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, Token, UserResponse, UserLogin
from ..services.auth_service import (
    authenticate_user, 
    create_access_token, 
    get_password_hash, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)

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