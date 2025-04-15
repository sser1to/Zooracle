from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from .database import Base

# Пример базовой модели
class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# Вы упомянули, что таблицы уже созданы
# Это просто примеры моделей, которые можно адаптировать под существующую схему
class User(BaseModel):
    __tablename__ = "users"
    
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

# Добавляйте другие модели в соответствии с вашей существующей схемой БД