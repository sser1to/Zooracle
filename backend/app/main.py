from fastapi import FastAPI, Depends, HTTPException  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session  # type: ignore
from sqlalchemy import text  # type: ignore
from typing import Optional
import os
import traceback

from .database import engine, get_db, init_db, Base
from .models import Base
from .routers import router, auth, animal_types, animals, habitats, media, tests, question, test_scores

# Создаем таблицы БД
Base.metadata.create_all(bind=engine)

# Инициализация приложения FastAPI
app = FastAPI(
    title="Zooracle API",
    description="API для приложения Zooracle",
    version="0.1.0"
)

# Настраиваем кроссдоменные запросы (CORS)
origins = [
    "http://localhost",       # Основной локальный хост
    "http://localhost:8080",  # Vue CLI dev server
    "http://localhost:8081",  # альтернативный порт Vue CLI
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8081",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Разрешаем запросы с указанных источников
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем любые HTTP-методы
    allow_headers=["*"],  # Разрешаем любые HTTP-заголовки
)

# Инициализируем структуру базы данных при запуске приложения
try:
    # Вызываем функцию инициализации БД
    init_db()
except Exception as e:
    print(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось инициализировать базу данных: {str(e)}")
    print("Детали ошибки:")
    traceback.print_exc()
    # В продакшн окружении можно завершить приложение здесь
    # import sys
    # sys.exit(1)

# Подключаем все API-маршруты через единый роутер
# Это объединяет все подроутеры из __init__.py
app.include_router(router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(animal_types.router, prefix="/api/animal-types")
app.include_router(animals.router, prefix="/api/animals")
app.include_router(habitats.router, prefix="/api/habitats")
app.include_router(media.router, prefix="/api/media")
app.include_router(tests.router, prefix="/api/tests")
app.include_router(question.router, prefix="/api/questions")
app.include_router(test_scores.router, prefix="/api/test-scores")  # Добавляем маршрутизатор для результатов тестов

@app.get("/")
async def root():
    """
    Корневой маршрут, возвращающий приветственное сообщение
    
    Returns:
        dict: Приветственное сообщение
    """
    return {"message": "Добро пожаловать в API Zooracle!"}

@app.get("/api/health")
def health_check():
    """
    Эндпоинт для проверки работоспособности API.
    
    Returns:
        dict: Статус работоспособности API
    """
    return {"status": "success", "message": "API is healthy"}

@app.get("/api/db-status")
def db_status(db: Session = Depends(get_db)):
    """
    Эндпоинт для проверки соединения с базой данных.
    
    Args:
        db (Session): Сессия базы данных (внедряется автоматически)
        
    Returns:
        dict: Статус соединения с базой данных
    """
    try:
        # Проверяем соединение с БД, выполнив простой запрос
        # Используем функцию text() для явного обозначения SQL запроса
        db.execute(text("SELECT 1"))
        return {"status": "success", "message": "Database connection is successful"}
    except Exception as e:
        return {"status": "error", "message": f"Database connection failed: {str(e)}"}

# Перехватываем все остальные GET-запросы, чтобы обрабатывать маршруты SPA
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    """
    Обрабатывает все GET-запросы, которые не были обработаны другими маршрутами
    
    Args:
        full_path (str): Полный путь запроса
        
    Returns:
        FileResponse: Файл index.html для рендеринга SPA
    """
    # Возвращаем index.html для всех маршрутов, чтобы VueRouter мог обрабатывать маршруты на стороне клиента
    return {"message": f"Маршрут не найден: {full_path}"}