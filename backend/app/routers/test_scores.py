from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any, Optional

from .. import models, schemas, database
from ..routers.auth import get_current_user

# Убираем префикс, чтобы избежать дублирования с main.py
router = APIRouter(
    tags=["test scores"]
)


def get_db():
    """
    Получение соединения с базой данных
    
    Yields:
        Session: Сессия базы данных для выполнения запросов
    """
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schemas.TestScore)
async def create_test_score(
    test_score: schemas.TestScoreCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Сохранение результатов прохождения теста
    
    Args:
        test_score (schemas.TestScoreCreate): Данные с результатами теста
            (ID теста, количество правильных ответов, общее количество вопросов)
        db (Session): Сессия БД
        current_user (schemas.UserResponse): Текущий пользователь
        
    Returns:
        models.TestScore: Сохраненный результат теста
        
    Raises:
        HTTPException: Если тест не найден
    """
    # Проверяем существование теста
    db_test = db.query(models.Test).filter(models.Test.id == test_score.test_id).first()
    if db_test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тест не найден"
        )
    
    # Форматируем результат в виде "X/Y"
    score_text = f"{test_score.correct_answers}/{test_score.total_questions}"
    
    # Создаем запись о результате теста
    db_test_score = models.TestScore(
        user_id=current_user.id,
        test_id=test_score.test_id,
        score=score_text,
        date=datetime.utcnow()
    )
    
    db.add(db_test_score)
    db.commit()
    db.refresh(db_test_score)
    
    return db_test_score


@router.get("/", response_model=List[schemas.TestScore])
async def get_user_test_scores(
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Получение всех результатов тестов текущего пользователя
    
    Args:
        db (Session): Сессия БД
        current_user (schemas.UserResponse): Текущий пользователь
        
    Returns:
        List[models.TestScore]: Список результатов тестов
    """
    return db.query(models.TestScore).filter(models.TestScore.user_id == current_user.id).all()


@router.get("/{test_id}", response_model=schemas.TestScore)
async def get_test_score(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Получение последнего результата конкретного теста пользователя
    
    Args:
        test_id (int): ID теста
        db (Session): Сессия БД
        current_user (schemas.UserResponse): Текущий пользователь
        
    Returns:
        models.TestScore: Результат теста
        
    Raises:
        HTTPException: Если результат не найден
    """
    db_test_score = db.query(models.TestScore).filter(
        models.TestScore.user_id == current_user.id,
        models.TestScore.test_id == test_id
    ).order_by(models.TestScore.date.desc()).first()
    
    if db_test_score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Результат теста не найден"
        )
    
    return db_test_score