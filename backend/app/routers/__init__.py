from fastapi import APIRouter, Depends, HTTPException, UploadFile, File # type: ignore
from sqlalchemy.orm import Session # type: ignore
from typing import List
import os

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserResponse
from ..services import minio_service
from .auth import router as auth_router
from .animals import router as animals_router
from .animal_types import router as animal_types_router
from .habitats import router as habitats_router
from .tests import router as tests_router
from .question import router as questions_router
from .media import router as media_router

# Создаем основной роутер API
router = APIRouter()

# Подключаем маршруты аутентификации
router.include_router(auth_router, prefix="/auth", tags=["auth"])

# Подключаем маршруты для работы с животными
router.include_router(animals_router, prefix="/animals", tags=["animals"])

# Подключаем маршруты для работы с типами животных
router.include_router(animal_types_router, prefix="/animal-types", tags=["animal-types"])

# Подключаем маршруты для работы с местами обитания
router.include_router(habitats_router, prefix="/habitats", tags=["habitats"])

# Подключаем маршруты для работы с тестами
router.include_router(tests_router, prefix="/tests", tags=["tests"])

# Подключаем маршруты для работы с вопросами
router.include_router(questions_router, prefix="/questions", tags=["questions"])

# Подключаем маршруты для работы с медиа-файлами
router.include_router(media_router, prefix="/media", tags=["media"])