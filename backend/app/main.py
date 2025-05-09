from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import os
import traceback
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import sys

from .database import engine, get_db, init_db, Base
from .models import Base
from .routers import router, auth, animal_types, animals, habitats, media, tests, question, test_scores

# Создаем таблицы БД
Base.metadata.create_all(bind=engine)

# Инициализация приложения FastAPI с настройкой для больших файлов
app = FastAPI(
    title="Zooracle API",
    description="API для приложения Zooracle",
    version="0.1.0"
)

# Класс middleware для увеличения лимита на размер файлов
class LargeFileMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        setattr(request.app.state, "max_content_length", 1024 * 1024 * 1024)
        response = await call_next(request)
        return response

# Добавляем middleware для больших файлов
app.add_middleware(LargeFileMiddleware)

# Настраиваем кроссдоменные запросы (CORS)
site_ip = os.environ.get("FRONTEND_URL", "").strip()
frontend_url = os.environ.get("FRONTEND_URL", "").strip()

# Формируем список разрешенных источников для CORS
origins = []

# Добавляем основные URL в список разрешенных источников
if site_ip:
    if not (site_ip.startswith("http://") or site_ip.startswith("https://")):
        origins.extend([f"http://{site_ip}", f"https://{site_ip}"])
    else:
        origins.append(site_ip)

if frontend_url:
    if not (frontend_url.startswith("http://") or frontend_url.startswith("https://")):
        origins.extend([f"http://{frontend_url}", f"https://{frontend_url}"])
    else:
        origins.append(frontend_url)

# Добавляем локальные URL для разработки
origins.extend([
    "http://localhost",
    "https://localhost",
    "http://localhost:8080",
    "https://localhost:8080",
    "http://localhost:3000",
    "https://localhost:3000",
])

origins = list(filter(None, set(origins)))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализируем структуру базы данных при запуске приложения
try:
    init_db()
except Exception as e:
    print(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось инициализировать базу данных: {str(e)}")
    print("Детали ошибки:")
    traceback.print_exc()

# Подключаем все API-маршруты через единый роутер
app.include_router(router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(animal_types.router, prefix="/api/animal-types")
app.include_router(animals.router, prefix="/api/animals")
app.include_router(habitats.router, prefix="/api/habitats")
app.include_router(media.router, prefix="/api/media")
app.include_router(tests.router, prefix="/api/tests")
app.include_router(question.router, prefix="/api/questions")
app.include_router(test_scores.router, prefix="/api/test-scores")

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