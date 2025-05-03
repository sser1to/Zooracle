from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List

from .. import models, schemas, database
from ..routers.auth import get_current_user, get_current_admin

# Убираем prefix, т.к. он уже задается в __init__.py
router = APIRouter(
    tags=["tests"]
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


@router.post("/", response_model=schemas.Test)
async def create_test(
    test: schemas.TestCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_admin)  # Используем get_current_admin
):
    """
    Создание нового теста
    
    Args:
        test (schemas.TestCreate): Данные для создания теста
        db (Session): Сессия БД
        current_user (schemas.UserResponse): Текущий пользователь (администратор)
        
    Returns:
        models.Test: Созданный тест
    """
    # Создаем новый тест
    db_test = models.Test(name=test.name)
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    
    # Если указан animal_id, обновляем ссылку на тест у животного
    if test.animal_id:
        db_animal = db.query(models.Animal).filter(models.Animal.id == test.animal_id).first()
        if db_animal:
            db_animal.test_id = db_test.id
            db.commit()
            db.refresh(db_animal)
    
    return db_test


@router.get("/", response_model=List[schemas.Test])
def get_tests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Получение списка всех тестов
    
    Args:
        skip (int, optional): Сколько записей пропустить. По умолчанию 0.
        limit (int, optional): Максимальное количество записей. По умолчанию 100.
        db (Session): Сессия БД
        
    Returns:
        List[models.Test]: Список тестов
    """
    return db.query(models.Test).offset(skip).limit(limit).all()


@router.get("/{test_id}", response_model=schemas.Test)
def get_test(
    test_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение теста по ID
    
    Args:
        test_id (int): ID теста
        db (Session): Сессия БД
        
    Returns:
        models.Test: Найденный тест
        
    Raises:
        HTTPException: Если тест не найден
    """
    db_test = db.query(models.Test).filter(models.Test.id == test_id).first()
    if db_test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тест не найден"
        )
    return db_test


@router.put("/{test_id}", response_model=schemas.Test)
async def update_test(
    test_id: int,
    test: schemas.TestUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_admin)  # Используем get_current_admin
):
    """
    Обновление теста по ID
    
    Args:
        test_id (int): ID теста для обновления
        test (schemas.TestUpdate): Данные для обновления
        db (Session): Сессия БД
        current_user (schemas.UserResponse): Текущий пользователь (администратор)
        
    Returns:
        models.Test: Обновленный тест
        
    Raises:
        HTTPException: Если тест не найден
    """
    db_test = db.query(models.Test).filter(models.Test.id == test_id).first()
    if db_test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тест не найден"
        )
    
    update_data = test.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_test, key, value)
    
    db.commit()
    db.refresh(db_test)
    return db_test


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_admin)  # Используем get_current_admin
):
    """
    Удаление теста по ID
    
    Args:
        test_id (int): ID теста для удаления
        db (Session): Сессия БД
        current_user (schemas.UserResponse): Текущий пользователь (администратор)
        
    Raises:
        HTTPException: Если тест не найден
    """
    db_test = db.query(models.Test).filter(models.Test.id == test_id).first()
    if db_test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тест не найден"
        )
    
    # Обновляем ссылки на тест в животных перед удалением
    db_animals = db.query(models.Animal).filter(models.Animal.test_id == test_id).all()
    for animal in db_animals:
        animal.test_id = None
    
    # Удаляем связи с вопросами
    db.query(models.TestQuestion).filter(models.TestQuestion.test_id == test_id).delete()
    
    # Удаляем тест
    db.delete(db_test)
    db.commit()
    
    return None


@router.get("/{test_id}/questions", response_model=List[schemas.Question])
def get_test_questions(
    test_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение всех вопросов теста по ID теста
    
    Args:
        test_id (int): ID теста
        db (Session): Сессия БД
        
    Returns:
        List[schemas.Question]: Список вопросов с вариантами ответов
        
    Raises:
        HTTPException: Если тест не найден
    """
    # Проверяем, существует ли тест
    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    if test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тест не найден"
        )
    
    # Получаем все ID вопросов, связанные с данным тестом
    test_question_relations = db.query(models.TestQuestion).filter(
        models.TestQuestion.test_id == test_id
    ).all()
    
    question_ids = [tq.question_id for tq in test_question_relations]
    
    # Если вопросов нет, возвращаем пустой список
    if not question_ids:
        return []
    
    # Получаем все вопросы по найденным ID
    questions = db.query(models.Question).filter(
        models.Question.id.in_(question_ids)
    ).all()
    
    # Для каждого вопроса получаем варианты ответов
    result = []
    for question in questions:
        # Получаем связи вопрос-ответ
        question_answer_relations = db.query(models.QuestionAnswer).filter(
            models.QuestionAnswer.question_id == question.id
        ).all()
        
        answer_ids = [qa.answer_id for qa in question_answer_relations]
        
        # Получаем варианты ответов
        answers = []
        if answer_ids:
            answers = db.query(models.AnswerOption).filter(
                models.AnswerOption.id.in_(answer_ids)
            ).all()
        
        # Создаем объект вопроса с вариантами ответов
        question_dict = {
            "id": question.id,
            "name": question.name,
            "question_type_id": question.question_type_id,
            "answers": answers
        }
        result.append(question_dict)
    
    return result


@router.post("/{test_id}/questions", response_model=List[schemas.Question])
async def create_or_update_test_questions(
    test_id: int,
    questions_data: schemas.TestQuestionsUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_admin)  # Используем get_current_admin
):
    """
    Создание или обновление вопросов теста
    
    Args:
        test_id (int): ID теста
        questions_data (schemas.TestQuestionsUpdate): Данные вопросов для создания/обновления
        db (Session): Сессия БД
        current_user (schemas.UserResponse): Текущий пользователь (администратор)
        
    Returns:
        List[schemas.Question]: Список созданных/обновленных вопросов
        
    Raises:
        HTTPException: Если тест не найден
    """
    # Проверяем, существует ли тест
    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    if test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тест не найден"
        )
    
    # Получаем все существующие связи вопросов с этим тестом
    existing_test_questions = db.query(models.TestQuestion).filter(
        models.TestQuestion.test_id == test_id
    ).all()
    
    # Получаем ID существующих вопросов
    existing_question_ids = [tq.question_id for tq in existing_test_questions]
    
    # Сохраняем новые вопросы и ответы
    result_questions = []
    
    # Добавляем новые вопросы и обновляем существующие
    for question_data in questions_data.questions:
        question_id = question_data.id
        
        if question_id:
            # Обновляем существующий вопрос
            question = db.query(models.Question).filter(models.Question.id == question_id).first()
            if question:
                question.name = question_data.name
                question.question_type_id = question_data.question_type_id
                db.commit()
                db.refresh(question)
            else:
                # Если ID указан, но вопрос не найден, создаем новый
                question = models.Question(
                    name=question_data.name,
                    question_type_id=question_data.question_type_id
                )
                db.add(question)
                db.commit()
                db.refresh(question)
                
                # Создаем связь вопроса с тестом
                test_question = models.TestQuestion(
                    test_id=test_id,
                    question_id=question.id
                )
                db.add(test_question)
                db.commit()
        else:
            # Создаем новый вопрос
            question = models.Question(
                name=question_data.name,
                question_type_id=question_data.question_type_id
            )
            db.add(question)
            db.commit()
            db.refresh(question)
            
            # Создаем связь вопроса с тестом
            test_question = models.TestQuestion(
                test_id=test_id,
                question_id=question.id
            )
            db.add(test_question)
            db.commit()
        
        # Обрабатываем варианты ответов для вопроса
        # Сначала получаем существующие связи вопрос-ответ
        existing_question_answers = db.query(models.QuestionAnswer).filter(
            models.QuestionAnswer.question_id == question.id
        ).all()
        
        # Получаем ID существующих ответов
        existing_answer_ids = []
        for qa in existing_question_answers:
            answer = db.query(models.AnswerOption).filter(models.AnswerOption.id == qa.answer_id).first()
            if answer:
                existing_answer_ids.append(answer.id)
        
        # Добавляем или обновляем варианты ответов
        new_answer_ids = []
        for answer_data in question_data.answers:
            if answer_data.id:
                # Обновляем существующий вариант ответа
                answer = db.query(models.AnswerOption).filter(models.AnswerOption.id == answer_data.id).first()
                if answer:
                    answer.name = answer_data.name
                    answer.is_correct = answer_data.is_correct
                    db.commit()
                    db.refresh(answer)
                    new_answer_ids.append(answer.id)
                else:
                    # Если ID указан, но вариант ответа не найден, создаем новый
                    answer = models.AnswerOption(
                        name=answer_data.name,
                        is_correct=answer_data.is_correct
                    )
                    db.add(answer)
                    db.commit()
                    db.refresh(answer)
                    new_answer_ids.append(answer.id)
                    
                    # Создаем связь вопрос-ответ
                    question_answer = models.QuestionAnswer(
                        question_id=question.id,
                        answer_id=answer.id
                    )
                    db.add(question_answer)
                    db.commit()
            else:
                # Создаем новый вариант ответа
                answer = models.AnswerOption(
                    name=answer_data.name,
                    is_correct=answer_data.is_correct
                )
                db.add(answer)
                db.commit()
                db.refresh(answer)
                new_answer_ids.append(answer.id)
                
                # Создаем связь вопрос-ответ
                question_answer = models.QuestionAnswer(
                    question_id=question.id,
                    answer_id=answer.id
                )
                db.add(question_answer)
                db.commit()
        
        # Удаляем варианты ответов, которых нет в новом списке
        for answer_id in existing_answer_ids:
            if answer_id not in new_answer_ids:
                # Удаляем связь вопрос-ответ
                db.query(models.QuestionAnswer).filter(
                    and_(
                        models.QuestionAnswer.question_id == question.id,
                        models.QuestionAnswer.answer_id == answer_id
                    )
                ).delete()
                
                # Удаляем вариант ответа
                db.query(models.AnswerOption).filter(models.AnswerOption.id == answer_id).delete()
                
        db.commit()
        
        # Добавляем обработанный вопрос в результат
        result_questions.append(question)
    
    # Получаем список ID вопросов после обработки
    processed_question_ids = [q.id for q in result_questions]
    
    # Удаляем вопросы, которых больше нет в тесте
    for question_id in existing_question_ids:
        if question_id not in processed_question_ids:
            # Удаляем связь тест-вопрос
            db.query(models.TestQuestion).filter(
                and_(
                    models.TestQuestion.test_id == test_id,
                    models.TestQuestion.question_id == question_id
                )
            ).delete()
            
            # Проверяем, используется ли вопрос в других тестах
            other_test_questions = db.query(models.TestQuestion).filter(
                models.TestQuestion.question_id == question_id
            ).all()
            
            # Если вопрос не используется в других тестах, удаляем его
            if not other_test_questions:
                # Получаем все связи вопрос-ответ
                question_answers = db.query(models.QuestionAnswer).filter(
                    models.QuestionAnswer.question_id == question_id
                ).all()
                
                # Удаляем все связи вопрос-ответ и ответы
                for qa in question_answers:
                    answer_id = qa.answer_id
                    
                    # Удаляем связь вопрос-ответ
                    db.query(models.QuestionAnswer).filter(
                        models.QuestionAnswer.id == qa.id
                    ).delete()
                    
                    # Удаляем вариант ответа
                    db.query(models.AnswerOption).filter(
                        models.AnswerOption.id == answer_id
                    ).delete()
                
                # Удаляем вопрос
                db.query(models.Question).filter(models.Question.id == question_id).delete()
            
            db.commit()
    
    # Получаем обновленный список вопросов с вариантами ответов
    return get_test_questions(test_id=test_id, db=db)


@router.post("/{test_id}/check")
async def check_test_answers(
    test_id: int,
    answers_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Проверка ответов пользователя на вопросы теста
    
    Args:
        test_id (int): ID теста
        answers_data (dict): Данные с ответами пользователя
        db (Session): Сессия БД
        current_user (schemas.UserResponse): Текущий пользователь
        
    Returns:
        dict: Результаты проверки теста
        
    Raises:
        HTTPException: Если тест не найден
    """
    # Проверяем существование теста
    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    if test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тест не найден"
        )
    
    # Получаем список вопросов теста
    test_question_relations = db.query(models.TestQuestion).filter(
        models.TestQuestion.test_id == test_id
    ).all()
    
    question_ids = [tq.question_id for tq in test_question_relations]
    
    # Если вопросов нет, возвращаем ошибку
    if not question_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="У теста отсутствуют вопросы"
        )
    
    # Получаем все вопросы теста с ответами
    questions_with_answers = []
    correct_answers = 0
    question_results = []
    
    # Получаем ответы пользователя
    user_answers = answers_data.get("answers", [])
    
    # Для каждого вопроса проверяем правильность ответов
    for question_id in question_ids:
        # Получаем вопрос
        question = db.query(models.Question).filter(models.Question.id == question_id).first()
        if not question:
            continue
        
        # Получаем связи вопрос-ответ
        question_answer_relations = db.query(models.QuestionAnswer).filter(
            models.QuestionAnswer.question_id == question_id
        ).all()
        
        answer_ids = [qa.answer_id for qa in question_answer_relations]
        
        # Получаем варианты ответов
        correct_answer_options = []
        if answer_ids:
            answers_query = db.query(models.AnswerOption).filter(
                models.AnswerOption.id.in_(answer_ids)
            ).all()
            
            # Фильтруем только правильные ответы
            correct_answer_options = [answer for answer in answers_query if answer.is_correct]
        
        # Находим ответ пользователя на этот вопрос
        user_answer = next((a for a in user_answers if a.get("question_id") == question_id), None)
        
        # Если ответ пользователя не найден, помечаем как неправильный
        if not user_answer:
            question_results.append({
                "question_id": question_id,
                "is_correct": False
            })
            continue
        
        # Проверка ответа в зависимости от типа вопроса
        is_correct = False
        
        # Вопрос с текстовым ответом
        if question.question_type_id == 1:
            # Для текстового ответа проверяем совпадение с правильным ответом (без учета регистра)
            user_text = user_answer.get("text_answer", "").strip().lower()
            
            # Проверяем на совпадение с любым из правильных ответов
            for correct_option in correct_answer_options:
                if correct_option.name.lower() == user_text:
                    is_correct = True
                    break
        
        # Вопрос с одним или несколькими вариантами ответов
        elif question.question_type_id in [2, 3]:
            user_selected = set(user_answer.get("selected_options", []))
            correct_ids = set(answer.id for answer in correct_answer_options)
            
            # Для радио-кнопок (один правильный ответ)
            if question.question_type_id == 2:
                # Правильно, если пользователь выбрал ровно один вариант и он правильный
                is_correct = len(user_selected) == 1 and user_selected == correct_ids
            
            # Для чекбоксов (множественный выбор)
            else:
                # Правильно, если выбраны все правильные ответы и никаких лишних
                is_correct = user_selected == correct_ids
        
        # Сохраняем результат для этого вопроса
        question_results.append({
            "question_id": question_id,
            "is_correct": is_correct
        })
        
        # Увеличиваем счетчик правильных ответов
        if is_correct:
            correct_answers += 1
    
    # Вычисляем процент правильных ответов
    total_questions = len(question_ids)
    score_percentage = int(round(correct_answers / total_questions * 100)) if total_questions > 0 else 0
    
    # Формируем результат проверки
    result = {
        "test_id": test_id,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "score_percentage": score_percentage,
        "question_results": question_results
    }
    
    return result