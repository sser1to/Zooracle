from fastapi import APIRouter, Depends, HTTPException # type: ignore
from sqlalchemy.orm import Session # type: ignore
from typing import List
from sqlalchemy.exc import SQLAlchemyError # type: ignore

from ..database import get_db
from ..models import Question, QuestionType, AnswerOption, QuestionAnswer
from ..schemas import (
    QuestionCreate, 
    QuestionResponse, 
    QuestionTypeCreate,
    QuestionTypeResponse,
    AnswerOptionCreate,
    AnswerOptionResponse,
    QuestionAnswerCreate,
    QuestionAnswerResponse
)
from ..services.auth_service import get_current_admin_user

router = APIRouter()

# Маршруты для типов вопросов
@router.post("/types/", response_model=QuestionTypeResponse)
async def create_question_type(
    question_type: QuestionTypeCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Создание нового типа вопроса (только для администраторов)
    
    Args:
        question_type: Данные о типе вопроса
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        QuestionTypeResponse: Созданный тип вопроса
    """
    # Проверка на дубликаты
    existing = db.query(QuestionType).filter(QuestionType.name == question_type.name).first()
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Тип вопроса с таким названием уже существует"
        )
    
    try:
        new_question_type = QuestionType(**question_type.dict())
        db.add(new_question_type)
        db.commit()
        db.refresh(new_question_type)
        return new_question_type
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании типа вопроса: {str(e)}")

@router.get("/types/", response_model=List[QuestionTypeResponse])
async def get_question_types(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Получение списка типов вопросов
    
    Args:
        skip: Сколько записей пропустить
        limit: Максимальное количество записей
        db: Сессия базы данных
        
    Returns:
        List[QuestionTypeResponse]: Список типов вопросов
    """
    question_types = db.query(QuestionType).offset(skip).limit(limit).all()
    return question_types

@router.get("/types/{type_id}", response_model=QuestionTypeResponse)
async def get_question_type(
    type_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение информации о конкретном типе вопроса
    
    Args:
        type_id: ID типа вопроса
        db: Сессия базы данных
        
    Returns:
        QuestionTypeResponse: Данные о типе вопроса
    """
    question_type = db.query(QuestionType).filter(QuestionType.id == type_id).first()
    if question_type is None:
        raise HTTPException(status_code=404, detail="Тип вопроса не найден")
    return question_type

@router.put("/types/{type_id}", response_model=QuestionTypeResponse)
async def update_question_type(
    type_id: int,
    question_type: QuestionTypeCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Обновление информации о типе вопроса (только для администраторов)
    
    Args:
        type_id: ID типа вопроса
        question_type: Новые данные о типе вопроса
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        QuestionTypeResponse: Обновленный тип вопроса
    """
    db_question_type = db.query(QuestionType).filter(QuestionType.id == type_id).first()
    if db_question_type is None:
        raise HTTPException(status_code=404, detail="Тип вопроса не найден")
    
    # Проверка на дубликаты при обновлении
    if question_type.name != db_question_type.name:
        existing = db.query(QuestionType).filter(QuestionType.name == question_type.name).first()
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Тип вопроса с таким названием уже существует"
            )
    
    # Обновляем атрибуты типа вопроса
    for key, value in question_type.dict().items():
        setattr(db_question_type, key, value)
    
    try:
        db.commit()
        db.refresh(db_question_type)
        return db_question_type
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении типа вопроса: {str(e)}")

@router.delete("/types/{type_id}")
async def delete_question_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Удаление типа вопроса (только для администраторов)
    
    Args:
        type_id: ID типа вопроса
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        dict: Сообщение об успешном удалении
    """
    db_question_type = db.query(QuestionType).filter(QuestionType.id == type_id).first()
    if db_question_type is None:
        raise HTTPException(status_code=404, detail="Тип вопроса не найден")
    
    try:
        db.delete(db_question_type)
        db.commit()
        return {"message": "Тип вопроса успешно удален"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении типа вопроса: {str(e)}")

# Маршруты для вопросов
@router.post("/", response_model=QuestionResponse)
async def create_question(
    question: QuestionCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Создание нового вопроса (только для администраторов)
    
    Args:
        question: Данные о вопросе
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        QuestionResponse: Созданный вопрос
    """
    # Проверяем существование типа вопроса
    question_type = db.query(QuestionType).filter(QuestionType.id == question.question_type_id).first()
    if question_type is None:
        raise HTTPException(status_code=404, detail="Тип вопроса не найден")
    
    try:
        new_question = Question(**question.dict())
        db.add(new_question)
        db.commit()
        db.refresh(new_question)
        return new_question
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании вопроса: {str(e)}")

@router.get("/", response_model=List[QuestionResponse])
async def get_questions(
    skip: int = 0, 
    limit: int = 100,
    question_type_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Получение списка вопросов с возможностью фильтрации по типу
    
    Args:
        skip: Сколько записей пропустить
        limit: Максимальное количество записей
        question_type_id: ID типа вопроса для фильтрации (опционально)
        db: Сессия базы данных
        
    Returns:
        List[QuestionResponse]: Список вопросов
    """
    query = db.query(Question)
    
    # Применяем фильтр по типу вопроса, если он указан
    if question_type_id:
        query = query.filter(Question.question_type_id == question_type_id)
    
    questions = query.offset(skip).limit(limit).all()
    return questions

@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение информации о конкретном вопросе
    
    Args:
        question_id: ID вопроса
        db: Сессия базы данных
        
    Returns:
        QuestionResponse: Данные о вопросе
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    return question

@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    question: QuestionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Обновление информации о вопросе (только для администраторов)
    
    Args:
        question_id: ID вопроса
        question: Новые данные о вопросе
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        QuestionResponse: Обновленный вопрос
    """
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if db_question is None:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
    # Проверяем существование типа вопроса при обновлении
    if question.question_type_id != db_question.question_type_id:
        question_type = db.query(QuestionType).filter(QuestionType.id == question.question_type_id).first()
        if question_type is None:
            raise HTTPException(status_code=404, detail="Тип вопроса не найден")
    
    # Обновляем атрибуты вопроса
    for key, value in question.dict().items():
        setattr(db_question, key, value)
    
    try:
        db.commit()
        db.refresh(db_question)
        return db_question
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении вопроса: {str(e)}")

@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Удаление вопроса (только для администраторов)
    
    Args:
        question_id: ID вопроса
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        dict: Сообщение об успешном удалении
    """
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if db_question is None:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
    try:
        db.delete(db_question)
        db.commit()
        return {"message": "Вопрос успешно удален"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении вопроса: {str(e)}")

# Маршруты для вариантов ответов
@router.post("/answers/", response_model=AnswerOptionResponse)
async def create_answer_option(
    answer: AnswerOptionCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Создание нового варианта ответа (только для администраторов)
    
    Args:
        answer: Данные о варианте ответа
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        AnswerOptionResponse: Созданный вариант ответа
    """
    try:
        new_answer = AnswerOption(**answer.dict())
        db.add(new_answer)
        db.commit()
        db.refresh(new_answer)
        return new_answer
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании варианта ответа: {str(e)}")

@router.get("/answers/", response_model=List[AnswerOptionResponse])
async def get_answer_options(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Получение списка вариантов ответов
    
    Args:
        skip: Сколько записей пропустить
        limit: Максимальное количество записей
        db: Сессия базы данных
        
    Returns:
        List[AnswerOptionResponse]: Список вариантов ответов
    """
    answers = db.query(AnswerOption).offset(skip).limit(limit).all()
    return answers

@router.put("/answers/{answer_id}", response_model=AnswerOptionResponse)
async def update_answer_option(
    answer_id: int,
    answer: AnswerOptionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Обновление информации о варианте ответа (только для администраторов)
    
    Args:
        answer_id: ID варианта ответа
        answer: Новые данные о варианте ответа
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        AnswerOptionResponse: Обновленный вариант ответа
    """
    db_answer = db.query(AnswerOption).filter(AnswerOption.id == answer_id).first()
    if db_answer is None:
        raise HTTPException(status_code=404, detail="Вариант ответа не найден")
    
    # Обновляем атрибуты варианта ответа
    for key, value in answer.dict().items():
        setattr(db_answer, key, value)
    
    try:
        db.commit()
        db.refresh(db_answer)
        return db_answer
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении варианта ответа: {str(e)}")

@router.delete("/answers/{answer_id}")
async def delete_answer_option(
    answer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Удаление варианта ответа (только для администраторов)
    
    Args:
        answer_id: ID варианта ответа
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        dict: Сообщение об успешном удалении
    """
    db_answer = db.query(AnswerOption).filter(AnswerOption.id == answer_id).first()
    if db_answer is None:
        raise HTTPException(status_code=404, detail="Вариант ответа не найден")
    
    try:
        db.delete(db_answer)
        db.commit()
        return {"message": "Вариант ответа успешно удален"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении варианта ответа: {str(e)}")

# Маршруты для связи вопросов и ответов
@router.post("/{question_id}/answers/", response_model=QuestionAnswerResponse)
async def link_answer_to_question(
    question_id: int,
    question_answer: QuestionAnswerCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Связывание вопроса с вариантом ответа (только для администраторов)
    
    Args:
        question_id: ID вопроса
        question_answer: Данные о связи вопроса с ответом
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        QuestionAnswerResponse: Созданная связь вопроса с ответом
    """
    # Проверяем существование вопроса
    question = db.query(Question).filter(Question.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
    # Проверяем существование варианта ответа
    answer = db.query(AnswerOption).filter(AnswerOption.id == question_answer.answer_id).first()
    if answer is None:
        raise HTTPException(status_code=404, detail="Вариант ответа не найден")
    
    # Проверяем, не связан ли уже этот вопрос с этим вариантом ответа
    existing = db.query(QuestionAnswer).filter(
        QuestionAnswer.question_id == question_id,
        QuestionAnswer.answer_id == question_answer.answer_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Этот вариант ответа уже связан с вопросом"
        )
    
    # Создаем новую связь вопроса с вариантом ответа
    new_question_answer = QuestionAnswer(
        question_id=question_id,
        answer_id=question_answer.answer_id
    )
    
    try:
        db.add(new_question_answer)
        db.commit()
        db.refresh(new_question_answer)
        return new_question_answer
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при связывании вопроса с вариантом ответа: {str(e)}")

@router.get("/{question_id}/answers/", response_model=List[QuestionAnswerResponse])
async def get_question_answers(
    question_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение всех вариантов ответов на вопрос
    
    Args:
        question_id: ID вопроса
        db: Сессия базы данных
        
    Returns:
        List[QuestionAnswerResponse]: Список связей вопроса с вариантами ответов
    """
    # Проверяем существование вопроса
    question = db.query(Question).filter(Question.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
    question_answers = db.query(QuestionAnswer).filter(QuestionAnswer.question_id == question_id).all()
    return question_answers

@router.delete("/{question_id}/answers/{answer_id}")
async def unlink_answer_from_question(
    question_id: int,
    answer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Удаление связи вопроса с вариантом ответа (только для администраторов)
    
    Args:
        question_id: ID вопроса
        answer_id: ID варианта ответа
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        dict: Сообщение об успешном удалении
    """
    question_answer = db.query(QuestionAnswer).filter(
        QuestionAnswer.question_id == question_id,
        QuestionAnswer.answer_id == answer_id
    ).first()
    
    if question_answer is None:
        raise HTTPException(status_code=404, detail="Связь вопроса с вариантом ответа не найдена")
    
    try:
        db.delete(question_answer)
        db.commit()
        return {"message": "Связь вопроса с вариантом ответа успешно удалена"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении связи вопроса с вариантом ответа: {str(e)}")