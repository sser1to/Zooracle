from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import os

from .database import engine, get_db
from .models import Base
from .routers import router

# Create tables if they don't exist
# Note: you mentioned tables are already created, so this will be a no-op
# if tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Zooracle API", version="0.1.0")

# Configure CORS - добавляем поддержку локального режима разработки
origins = [
    "http://localhost:8080",  # Vue CLI dev server
    "http://localhost:8081",  # альтернативный порт Vue CLI
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8081"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to Zooracle API"}

@app.get("/health")
def health_check():
    return {"status": "success", "message": "API is healthy"}

@app.get("/db-status")
def db_status(db: Session = Depends(get_db)):
    try:
        # Проверяем соединение с БД, выполнив простой запрос
        # Используем функцию text() для явного объявления текстового SQL-выражения
        db.execute(text("SELECT 1"))
        return {"status": "success", "message": "Database connection is successful"}
    except Exception as e:
        return {"status": "error", "message": f"Database connection failed: {str(e)}"}