from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List

from .. import models, schemas, database
from ..routers.auth import get_current_user

router = APIRouter(
    prefix="/questions",
    tags=["questions"]
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


@router.get("/types", response_model=List[schemas.QuestionType])
def get_question_types(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Получение списка всех типов вопросов
    
    Args:
        skip (int, optional): Сколько записей пропустить. По умолчанию 0.
        limit (int, optional): Максимальное количество записей. По умолчанию 100.
        db (Session): Сессия БД
        
    Returns:
        List[schemas.QuestionType]: Список типов вопросов
    """
    return db.query(models.QuestionType).offset(skip).limit(limit).all()


@router.post("/", response_model=schemas.Question)
def create_question(
    question: schemas.QuestionCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Создание нового вопроса
    
    Args:
        question (schemas.QuestionCreate): Данные для создания вопроса
        db (Session): Сессия БД
        current_user (schemas.UserResponse): Текущий пользователь
        
    Returns:
        models.Question: Созданный вопрос с вариантами ответов
        
    Raises:
        HTTPException: Если пользователь не авторизован или произошла ошибка
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Для создания вопросов необходимы права администратора"
        )
    
    # Проверяем существование типа вопроса
    question_type = db.query(models.QuestionType).filter(
        models.QuestionType.id == question.question_type_id
    ).first()
    
    if not question_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Тип вопроса с ID {question.question_type_id} не найден"
        )
    
    # Создаем вопрос
    db_question = models.Question(
        name=question.name,
        question_type_id=question.question_type_id
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    
    # Создаем варианты ответов и связи с вопросом
    answers = []
    for answer_data in question.answers:
        db_answer = models.AnswerOption(
            name=answer_data.name,
            is_correct=answer_data.is_correct
        )
        db.add(db_answer)
        db.commit()
        db.refresh(db_answer)
        
        # Создаем связь между вопросом и вариантом ответа
        db_question_answer = models.QuestionAnswer(
            question_id=db_question.id,
            answer_id=db_answer.id
        )
        db.add(db_question_answer)
        db.commit()
        
        answers.append(db_answer)
    
    # Формируем ответ с данными вопроса и вариантами ответов
    result = {
        "id": db_question.id,
        "name": db_question.name,
        "question_type_id": db_question.question_type_id,
        "answers": answers
    }
    
    return result


@router.get("/{question_id}", response_model=schemas.Question)
def get_question(
    question_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение вопроса по ID с вариантами ответов
    
    Args:
        question_id (int): ID вопроса
        db (Session): Сессия БД
        
    Returns:
        schemas.Question: Вопрос с вариантами ответов
        
    Raises:
        HTTPException: Если вопрос не найден
    """
    db_question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if db_question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вопрос не найден"
        )
    
    # Получаем связи вопрос-ответ
    question_answer_relations = db.query(models.QuestionAnswer).filter(
        models.QuestionAnswer.question_id == question_id
    ).all()
    
    answer_ids = [qa.answer_id for qa in question_answer_relations]
    
    # Получаем варианты ответов
    answers = []
    if answer_ids:
        answers = db.query(models.AnswerOption).filter(
            models.AnswerOption.id.in_(answer_ids)
        ).all()
    
    # Формируем ответ с данными вопроса и вариантами ответов
    result = {
        "id": db_question.id,
        "name": db_question.name,
        "question_type_id": db_question.question_type_id,
        "answers": answers
    }
    
    return result


@router.put("/{question_id}", response_model=schemas.Question)
def update_question(
    question_id: int,
    question_update: schemas.QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Обновление вопроса по ID
    
    Args:
        question_id (int): ID вопроса для обновления
        question_update (schemas.QuestionUpdate): Данные для обновления
        db (Session): Сессия БД
        current_user (schemas.UserResponse): Текущий пользователь
        
    Returns:
        schemas.Question: Обновленный вопрос с вариантами ответов
        
    Raises:
        HTTPException: Если вопрос не найден или пользователь не авторизован
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Для обновления вопросов необходимы права администратора"
        )
    
    db_question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if db_question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вопрос не найден"
        )
    
    # Обновляем данные вопроса
    update_data = question_update.dict(exclude_unset=True, exclude={"answers"})
    for key, value in update_data.items():
        setattr(db_question, key, value)
    
    db.commit()
    db.refresh(db_question)
    
    # Если переданы варианты ответов, обновляем их
    if question_update.answers is not None:
        # Получаем текущие связи вопрос-ответ
        existing_question_answers = db.query(models.QuestionAnswer).filter(
            models.QuestionAnswer.question_id == question_id
        ).all()
        
        existing_answer_ids = []
        for qa in existing_question_answers:
            existing_answer_ids.append(qa.answer_id)
        
        # Получаем существующие ответы
        existing_answers = {}
        if existing_answer_ids:
            answers_query = db.query(models.AnswerOption).filter(
                models.AnswerOption.id.in_(existing_answer_ids)
            ).all()
            existing_answers = {answer.id: answer for answer in answers_query}
        
        # Обрабатываем новые варианты ответов
        new_answer_ids = []
        for answer_data in question_update.answers:
            if answer_data.id and answer_data.id in existing_answers:
                # Обновляем существующий вариант ответа
                answer = existing_answers[answer_data.id]
                answer.name = answer_data.name
                answer.is_correct = answer_data.is_correct
                db.commit()
                db.refresh(answer)
                new_answer_ids.append(answer.id)
            else:
                # Создаем новый вариант ответа
                db_answer = models.AnswerOption(
                    name=answer_data.name,
                    is_correct=answer_data.is_correct
                )
                db.add(db_answer)
                db.commit()
                db.refresh(db_answer)
                
                # Создаем связь между вопросом и вариантом ответа
                db_question_answer = models.QuestionAnswer(
                    question_id=db_question.id,
                    answer_id=db_answer.id
                )
                db.add(db_question_answer)
                db.commit()
                
                new_answer_ids.append(db_answer.id)
        
        # Удаляем варианты ответов, которых нет в новом списке
        for answer_id in existing_answer_ids:
            if answer_id not in new_answer_ids:
                # Удаляем связь вопрос-ответ
                db.query(models.QuestionAnswer).filter(
                    and_(
                        models.QuestionAnswer.question_id == question_id,
                        models.QuestionAnswer.answer_id == answer_id
                    )
                ).delete()
                
                # Удаляем вариант ответа
                db.query(models.AnswerOption).filter(models.AnswerOption.id == answer_id).delete()
                
        db.commit()
    
    # Возвращаем обновленный вопрос с вариантами ответов
    return get_question(question_id=question_id, db=db)


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Удаление вопроса по ID
    
    Args:
        question_id (int): ID вопроса для удаления
        db (Session): Сессия БД
        current_user (schemas.UserResponse): Текущий пользователь
        
    Raises:
        HTTPException: Если вопрос не найден или пользователь не авторизован
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Для удаления вопросов необходимы права администратора"
        )
    
    db_question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if db_question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вопрос не найден"
        )
    
    # Удаляем связи тест-вопрос
    db.query(models.TestQuestion).filter(models.TestQuestion.question_id == question_id).delete()
    
    # Получаем все связи вопрос-ответ
    question_answers = db.query(models.QuestionAnswer).filter(
        models.QuestionAnswer.question_id == question_id
    ).all()
    
    # Удаляем все связи вопрос-ответ и ответы
    for qa in question_answers:
        answer_id = qa.answer_id
        
        # Удаляем связь вопрос-ответ
        db.query(models.QuestionAnswer).filter(models.QuestionAnswer.id == qa.id).delete()
        
        # Удаляем вариант ответа
        db.query(models.AnswerOption).filter(models.AnswerOption.id == answer_id).delete()
    
    # Удаляем вопрос
    db.delete(db_question)
    db.commit()
    
    return None