from fastapi import APIRouter, Depends, HTTPException # type: ignore
from sqlalchemy.orm import Session # type: ignore
from typing import List
from sqlalchemy.exc import SQLAlchemyError # type: ignore
from datetime import datetime

from ..database import get_db
from ..models import Test, TestQuestion, Question, TestScore
from ..schemas import (
    TestCreate, 
    TestResponse, 
    TestQuestionCreate, 
    TestQuestionResponse,
    TestScoreCreate,
    TestScoreResponse
)
from ..services.auth_service import get_current_user, get_current_admin_user

router = APIRouter()

@router.post("/", response_model=TestResponse)
async def create_test(
    test: TestCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Создание нового теста (только для администраторов)
    
    Args:
        test: Данные о тесте
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        TestResponse: Созданный тест
    """
    try:
        new_test = Test(**test.dict())
        db.add(new_test)
        db.commit()
        db.refresh(new_test)
        return new_test
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании теста: {str(e)}")

@router.get("/", response_model=List[TestResponse])
async def get_tests(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Получение списка тестов
    
    Args:
        skip: Сколько записей пропустить
        limit: Максимальное количество записей
        db: Сессия базы данных
        
    Returns:
        List[TestResponse]: Список тестов
    """
    tests = db.query(Test).offset(skip).limit(limit).all()
    return tests

@router.get("/{test_id}", response_model=TestResponse)
async def get_test(
    test_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение информации о конкретном тесте
    
    Args:
        test_id: ID теста
        db: Сессия базы данных
        
    Returns:
        TestResponse: Данные о тесте
    """
    test = db.query(Test).filter(Test.id == test_id).first()
    if test is None:
        raise HTTPException(status_code=404, detail="Тест не найден")
    return test

@router.put("/{test_id}", response_model=TestResponse)
async def update_test(
    test_id: int,
    test: TestCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Обновление информации о тесте (только для администраторов)
    
    Args:
        test_id: ID теста
        test: Новые данные о тесте
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        TestResponse: Обновленный тест
    """
    db_test = db.query(Test).filter(Test.id == test_id).first()
    if db_test is None:
        raise HTTPException(status_code=404, detail="Тест не найден")
    
    # Обновляем атрибуты теста
    for key, value in test.dict().items():
        setattr(db_test, key, value)
    
    try:
        db.commit()
        db.refresh(db_test)
        return db_test
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении теста: {str(e)}")

@router.delete("/{test_id}")
async def delete_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Удаление теста (только для администраторов)
    
    Args:
        test_id: ID теста
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        dict: Сообщение об успешном удалении
    """
    db_test = db.query(Test).filter(Test.id == test_id).first()
    if db_test is None:
        raise HTTPException(status_code=404, detail="Тест не найден")
    
    try:
        db.delete(db_test)
        db.commit()
        return {"message": "Тест успешно удален"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении теста: {str(e)}")

# Маршруты для связи тестов и вопросов
@router.post("/{test_id}/questions/", response_model=TestQuestionResponse)
async def add_question_to_test(
    test_id: int,
    test_question: TestQuestionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Добавление вопроса к тесту (только для администраторов)
    
    Args:
        test_id: ID теста
        test_question: Данные о связи теста с вопросом
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        TestQuestionResponse: Созданная связь теста с вопросом
    """
    # Проверяем существование теста
    test = db.query(Test).filter(Test.id == test_id).first()
    if test is None:
        raise HTTPException(status_code=404, detail="Тест не найден")
    
    # Проверяем существование вопроса
    question = db.query(Question).filter(Question.id == test_question.question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
    # Проверяем, не добавлен ли уже этот вопрос к тесту
    existing = db.query(TestQuestion).filter(
        TestQuestion.test_id == test_id,
        TestQuestion.question_id == test_question.question_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Этот вопрос уже добавлен к тесту"
        )
    
    # Создаем новую связь теста с вопросом
    new_test_question = TestQuestion(
        test_id=test_id,
        question_id=test_question.question_id
    )
    
    try:
        db.add(new_test_question)
        db.commit()
        db.refresh(new_test_question)
        return new_test_question
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при добавлении вопроса к тесту: {str(e)}")

@router.get("/{test_id}/questions/", response_model=List[TestQuestionResponse])
async def get_test_questions(
    test_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение всех вопросов теста
    
    Args:
        test_id: ID теста
        db: Сессия базы данных
        
    Returns:
        List[TestQuestionResponse]: Список связей теста с вопросами
    """
    # Проверяем существование теста
    test = db.query(Test).filter(Test.id == test_id).first()
    if test is None:
        raise HTTPException(status_code=404, detail="Тест не найден")
    
    test_questions = db.query(TestQuestion).filter(TestQuestion.test_id == test_id).all()
    return test_questions

@router.delete("/{test_id}/questions/{question_id}")
async def remove_question_from_test(
    test_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Удаление вопроса из теста (только для администраторов)
    
    Args:
        test_id: ID теста
        question_id: ID вопроса
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        dict: Сообщение об успешном удалении
    """
    test_question = db.query(TestQuestion).filter(
        TestQuestion.test_id == test_id,
        TestQuestion.question_id == question_id
    ).first()
    
    if test_question is None:
        raise HTTPException(status_code=404, detail="Вопрос не найден в тесте")
    
    try:
        db.delete(test_question)
        db.commit()
        return {"message": "Вопрос успешно удален из теста"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении вопроса из теста: {str(e)}")

# Маршруты для результатов тестов
@router.post("/{test_id}/scores/", response_model=TestScoreResponse)
async def submit_test_score(
    test_id: int,
    score: TestScoreCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Отправка результата теста
    
    Args:
        test_id: ID теста
        score: Данные о результате теста
        db: Сессия базы данных
        current_user: Текущий пользователь
        
    Returns:
        TestScoreResponse: Сохраненный результат теста
    """
    # Проверяем существование теста
    test = db.query(Test).filter(Test.id == test_id).first()
    if test is None:
        raise HTTPException(status_code=404, detail="Тест не найден")
    
    # Создаем новый результат теста
    new_score = TestScore(
        user_id=current_user.id,
        test_id=test_id,
        score=score.score,
        date=datetime.utcnow()
    )
    
    try:
        db.add(new_score)
        db.commit()
        db.refresh(new_score)
        return new_score
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении результата теста: {str(e)}")

@router.get("/{test_id}/scores/", response_model=List[TestScoreResponse])
async def get_test_scores(
    test_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Получение всех результатов теста (только для администраторов)
    
    Args:
        test_id: ID теста
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        List[TestScoreResponse]: Список результатов теста
    """
    # Проверяем существование теста
    test = db.query(Test).filter(Test.id == test_id).first()
    if test is None:
        raise HTTPException(status_code=404, detail="Тест не найден")
    
    scores = db.query(TestScore).filter(TestScore.test_id == test_id).all()
    return scores

@router.get("/user/scores/", response_model=List[TestScoreResponse])
async def get_user_scores(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Получение всех результатов тестов текущего пользователя
    
    Args:
        db: Сессия базы данных
        current_user: Текущий пользователь
        
    Returns:
        List[TestScoreResponse]: Список результатов тестов пользователя
    """
    scores = db.query(TestScore).filter(TestScore.user_id == current_user.id).all()
    return scores