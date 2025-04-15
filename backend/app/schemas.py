from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Базовая схема пользователя
class UserBase(BaseModel):
    username: str
    email: EmailStr

# Схема для создания пользователя
class UserCreate(UserBase):
    password: str

# Схема для ответа с данными пользователя
class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# Добавьте здесь другие схемы для моделей данных