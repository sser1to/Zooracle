from fastapi import FastAPI, Depends, HTTPException # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from sqlalchemy.orm import Session # type: ignore
from sqlalchemy import text # type: ignore
import os
import traceback

from .database import engine, get_db, init_db
from .models import Base
from .routers import router

# Инициализация приложения FastAPI
app = FastAPI(title="Zooracle API", version="0.1.0")

# Настраиваем кроссдоменные запросы (CORS)
origins = [
    "http://localhost:8080",  # Vue CLI dev server
    "https://localhost:8080", # HTTPS вариант для локального Vue CLI сервера
    "http://localhost:8081",  # альтернативный порт Vue CLI
    "https://localhost:8081", # HTTPS вариант для альтернативного порта Vue CLI
    "http://localhost:443",   # стандартный HTTPS порт
    "https://localhost:443",  # стандартный HTTPS порт
    "http://localhost:3000",  # на случай, если используется другой порт
    "https://localhost:3000", # HTTPS вариант
    "http://127.0.0.1:8080",
    "https://127.0.0.1:8080",
    "http://127.0.0.1:8081",
    "https://127.0.0.1:8081", 
    "http://127.0.0.1:443",
    "https://127.0.0.1:443",
    "http://127.0.0.1:3000",
    "https://127.0.0.1:3000",
    "electron://altair",      # Для Electron-приложения
    "file://"                 # Для доступа к файловой системе в Electron
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,    # Используем конкретные источники
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Подключаем все API-маршруты
app.include_router(router, prefix="/api")

@app.get("/")
def read_root():
    """
    Корневой маршрут API.
    
    Returns:
        dict: Приветственное сообщение
    """
    return {"message": "Welcome to Zooracle API"}

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