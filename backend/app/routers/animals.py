from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Literal
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, desc, asc

from ..database import get_db
from ..models import Animal, AnimalPhoto, AnimalType, Habitat, FavoriteAnimal, User
from ..schemas import (
    AnimalCreate, 
    AnimalResponse, 
    AnimalDetailResponse,
    AnimalPhotoCreate,
    AnimalPhotoResponse,
    FavoriteAnimalCreate,
    FavoriteAnimalResponse,
    AnimalBase
)
from ..services.auth_service import get_current_user, get_current_admin_user
from ..services.minio_service import delete_files_by_ids

# Определяем возможные расширения для изображений и видео
ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
ALLOWED_VIDEO_EXTENSIONS = [".mp4", ".avi"]

# Категории файлов
FILE_CATEGORIES = ["images", "videos"]

router = APIRouter()

@router.post("/", response_model=AnimalResponse)
async def create_animal(
    animal: AnimalCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Создание нового животного (только для администраторов)
    
    Args:
        animal: Данные о животном
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        AnimalResponse: Созданное животное
    """
    try:
        new_animal = Animal(**animal.dict())
        db.add(new_animal)
        db.commit()
        db.refresh(new_animal)
        return new_animal
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании животного: {str(e)}")

@router.get("/", response_model=List[AnimalResponse])
async def get_animals(
    skip: int = 0, 
    limit: int = 10000,
    search: Optional[str] = None,
    animal_type_id: Optional[int] = None,
    habitat_id: Optional[int] = None,
    sort_by: Optional[Literal["name", "id"]] = "id",
    sort_order: Optional[Literal["asc", "desc"]] = "asc",
    favorites_only: bool = False,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получение списка животных с возможностью поиска, фильтрации и сортировки
    
    Args:
        skip: Сколько записей пропустить
        limit: Максимальное количество записей (по умолчанию установлено большое значение для отображения всех записей)
        search: Строка поиска по названию
        animal_type_id: ID типа животного для фильтрации
        habitat_id: ID места обитания для фильтрации
        sort_by: Поле для сортировки ('name' или 'id')
        sort_order: Порядок сортировки ('asc' или 'desc')
        favorites_only: Фильтровать только избранные для текущего пользователя
        current_user: Текущий пользователь
        db: Сессия базы данных
        
    Returns:
        List[AnimalResponse]: Отфильтрованный и отсортированный список всех животных
    """
    query = db.query(Animal)
    
    # Применяем поиск по названию, если указан
    if search:
        query = query.filter(Animal.name.ilike(f"%{search}%"))
    
    # Применяем фильтры, если они указаны
    if animal_type_id:
        query = query.filter(Animal.animal_type_id == animal_type_id)
    if habitat_id:
        query = query.filter(Animal.habitat_id == habitat_id)
    
    # Фильтруем по избранным, если запрошено и пользователь авторизован
    if favorites_only and current_user:
        favorite_animal_ids = db.query(FavoriteAnimal.animal_id).filter(
            FavoriteAnimal.user_id == current_user.id
        ).subquery()
        
        # Фильтруем животных по подзапросу
        query = query.filter(Animal.id.in_(favorite_animal_ids))
    
    # Применяем сортировку
    if sort_by == "name":
        if sort_order == "desc":
            query = query.order_by(desc(Animal.name))
        else:
            query = query.order_by(asc(Animal.name))
    else:  # По умолчанию сортируем по ID
        if sort_order == "desc":
            query = query.order_by(desc(Animal.id))
        else:
            query = query.order_by(asc(Animal.id))
    
    # Получаем результаты с пагинацией
    animals = query.offset(skip).limit(limit).all()
    return animals

@router.get("/{animal_id}", response_model=AnimalDetailResponse)
async def get_animal(
    animal_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение информации о конкретном животном
    
    Args:
        animal_id: ID животного
        db: Сессия базы данных
        
    Returns:
        AnimalDetailResponse: Данные о животном
    """
    animal = db.query(Animal).filter(Animal.id == animal_id).first()
    if animal is None:
        raise HTTPException(status_code=404, detail="Животное не найдено")
    return animal

@router.put("/{animal_id}", response_model=AnimalResponse)
async def update_animal(
    animal_id: int,
    animal_data: AnimalBase,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Обновление информации о животном (только для администраторов)
    
    Поддерживает частичное обновление полей животного (PATCH).
    Можно обновлять только нужные поля, остальные останутся без изменений.
    
    Args:
        animal_id: ID животного
        animal_data: Данные для обновления (любые поля модели)
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        AnimalResponse: Обновленное животное
    """
    # Получаем животное из БД
    db_animal = db.query(Animal).filter(Animal.id == animal_id).first()
    if db_animal is None:
        raise HTTPException(status_code=404, detail="Животное не найдено")
    
    # Получаем только заполненные поля (не None)
    update_data = {k: v for k, v in animal_data.dict().items() if v is not None}
    
    # Если нет полей для обновления, возвращаем существующее животное
    if not update_data:
        return db_animal
    
    try:
        # Обновляем только указанные поля
        for key, value in update_data.items():
            setattr(db_animal, key, value)
        
        db.commit()
        db.refresh(db_animal)
        return db_animal
    except SQLAlchemyError as e:
        db.rollback()
        print(f"ОШИБКА при работе с сессией БД: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении животного: {str(e)}")

@router.delete("/{animal_id}")
async def delete_animal(
    animal_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Удаление животного (только для администраторов).
    При удалении животного также удаляется:
    1. Связанный тест (если есть)
    2. Все вопросы теста
    3. Все связи вопросов с вариантами ответов
    4. Все варианты ответов для вопросов
    5. Все результаты прохождения теста пользователями
    6. Все связанные медиафайлы (изображения, видео)
    
    Args:
        animal_id: ID животного
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        dict: Сообщение об успешном удалении
    """
    # Находим животное по ID
    db_animal = db.query(Animal).filter(Animal.id == animal_id).first()
    if db_animal is None:
        raise HTTPException(status_code=404, detail="Животное не найдено")
    
    try:
        # Собираем все идентификаторы файлов для удаления с вариантами путей в MinIO
        file_patterns_to_delete = []
        
        # Проверяем наличие связанного теста и удаляем его со всеми зависимостями
        if db_animal.test_id:
            try:
                from ..models import Test, TestQuestion, Question, QuestionAnswer, AnswerOption, TestScore
                
                test_id = db_animal.test_id
                print(f"Обнаружен связанный тест с ID: {test_id}. Начинаем процесс каскадного удаления.")
                
                # Удаление результатов теста (test_scores)
                test_scores = db.query(TestScore).filter(TestScore.test_id == test_id).all()
                scores_count = len(test_scores)
                for score in test_scores:
                    db.delete(score)
                print(f"Удалено {scores_count} результатов теста с ID {test_id}")
                
                # Получаем все вопросы теста через связь TestQuestion
                test_questions = db.query(TestQuestion).filter(TestQuestion.test_id == test_id).all()
                question_ids = [tq.question_id for tq in test_questions]
                
                print(f"Найдено {len(question_ids)} вопросов, связанных с тестом {test_id}: {question_ids}")
                
                # Для каждого вопроса удаляем связи с вариантами ответов
                for question_id in question_ids:
                    # Получаем все связи вопроса с вариантами ответов
                    question_answers = db.query(QuestionAnswer).filter(
                        QuestionAnswer.question_id == question_id
                    ).all()
                    
                    # Собираем ID ответов для последующего удаления
                    answer_ids = [qa.answer_id for qa in question_answers]
                    
                    print(f"Для вопроса {question_id} найдено {len(question_answers)} связей с вариантами ответов")
                    
                    # Удаляем связи вопросов с ответами
                    for qa in question_answers:
                        db.delete(qa)
                    
                    # Удаляем связь вопроса с тестом из таблицы TestQuestion
                    test_question = db.query(TestQuestion).filter(
                        TestQuestion.test_id == test_id,
                        TestQuestion.question_id == question_id
                    ).first()
                    if test_question:
                        db.delete(test_question)
                    
                    # Удаляем сам вопрос
                    question = db.query(Question).filter(Question.id == question_id).first()
                    if question:
                        db.delete(question)
                    
                    # Удаляем варианты ответов
                    for answer_id in answer_ids:
                        answer = db.query(AnswerOption).filter(AnswerOption.id == answer_id).first()
                        if answer:
                            db.delete(answer)
                
                # Удаляем сам тест
                test = db.query(Test).filter(Test.id == test_id).first()
                if test:
                    db.delete(test)
                    print(f"Тест с ID {test_id} и все связанные данные успешно удалены")
                
            except Exception as e:
                print(f"Ошибка при каскадном удалении теста: {str(e)}")
        
        # Добавляем все возможные варианты пути для обложки
        if db_animal.preview_id:
            for ext in ALLOWED_IMAGE_EXTENSIONS:
                for category in FILE_CATEGORIES:
                    file_patterns_to_delete.append(f"{category}/{db_animal.preview_id}{ext}")
        
        # Добавляем все возможные варианты пути для видео
        if db_animal.video_id:
            for ext in ALLOWED_VIDEO_EXTENSIONS:
                file_patterns_to_delete.append(f"videos/{db_animal.video_id}{ext}")
            for ext in ALLOWED_VIDEO_EXTENSIONS:
                file_patterns_to_delete.append(f"images/{db_animal.video_id}{ext}")
        
        # Получаем и добавляем все возможные варианты путей для фотографий
        photos = db.query(AnimalPhoto).filter(AnimalPhoto.animal_id == animal_id).all()
        for photo in photos:
            if photo.photo_id:
                for ext in ALLOWED_IMAGE_EXTENSIONS:
                    file_patterns_to_delete.append(f"images/{photo.photo_id}{ext}")
        
        print(f"Всего путей для поиска и удаления файлов: {len(file_patterns_to_delete)}")
        print(f"Пути для удаления: {file_patterns_to_delete}")
        
        # Удаляем животное из базы данных
        db.delete(db_animal)
        db.commit()
        
        # Удаляем все связанные файлы из MinIO после успешного удаления из БД
        if file_patterns_to_delete:
            deletion_result = await delete_files_by_ids(file_patterns_to_delete)
            print(f"Результат удаления файлов из MinIO: {deletion_result}")
        
        return {"message": "Животное и все связанные с ним данные успешно удалены"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении животного: {str(e)}")
    except Exception as e:
        return {
            "message": "Животное удалено, но возникли проблемы при удалении некоторых файлов",
            "error": str(e)
        }

# Маршруты для работы с фотографиями животных

@router.post("/{animal_id}/photos/", response_model=AnimalPhotoResponse)
async def add_photo(
    animal_id: int,
    photo: AnimalPhotoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Добавление фото к животному (только для администраторов)
    
    Args:
        animal_id: ID животного (из пути URL)
        photo: Данные о фотографии (содержит только photo_id)
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        AnimalPhotoResponse: Добавленная фотография
    """
    # Проверяем существование животного
    animal = db.query(Animal).filter(Animal.id == animal_id).first()
    if animal is None:
        raise HTTPException(status_code=404, detail="Животное не найдено")
    
    # Создаем новую фотографию, используя animal_id из пути и photo_id из тела запроса
    new_photo = AnimalPhoto(animal_id=animal_id, photo_id=photo.photo_id)
    
    try:
        db.add(new_photo)
        db.commit()
        db.refresh(new_photo)
        return new_photo
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при добавлении фото: {str(e)}")

@router.get("/{animal_id}/photos/", response_model=List[AnimalPhotoResponse])
async def get_animal_photos(
    animal_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение всех фотографий животного
    
    Args:
        animal_id: ID животного
        db: Сессия базы данных
        
    Returns:
        List[AnimalPhotoResponse]: Список фотографий
    """
    # Проверяем существование животного
    animal = db.query(Animal).filter(Animal.id == animal_id).first()
    if animal is None:
        raise HTTPException(status_code=404, detail="Животное не найдено")
    
    photos = db.query(AnimalPhoto).filter(AnimalPhoto.animal_id == animal_id).all()
    return photos

@router.delete("/{animal_id}/photos/{photo_id}")
async def delete_animal_photo(
    animal_id: int,
    photo_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Удаление фотографии животного (только для администраторов)
    
    Args:
        animal_id: ID животного
        photo_id: ID фотографии (строковый идентификатор)
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        dict: Сообщение об успешном удалении
    """
    photo = db.query(AnimalPhoto).filter(
        AnimalPhoto.photo_id == photo_id, 
        AnimalPhoto.animal_id == animal_id
    ).first()
    
    if photo is None:
        raise HTTPException(status_code=404, detail="Фото не найдено")
    
    try:
        # Формируем все возможные пути файла в MinIO
        file_patterns_to_delete = []
        for ext in ALLOWED_IMAGE_EXTENSIONS:
            file_patterns_to_delete.append(f"images/{photo_id}{ext}")
            
        # Удаляем запись из базы данных
        db.delete(photo)
        db.commit()
        
        # Удаляем файл из MinIO
        if file_patterns_to_delete:
            deletion_result = await delete_files_by_ids(file_patterns_to_delete)
            print(f"Результат удаления файла из MinIO: {deletion_result}")
            
        return {"message": "Фото успешно удалено"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении фото: {str(e)}")
    except Exception as e:
        return {
            "message": "Запись о фото удалена, но возникли проблемы при удалении файла",
            "error": str(e)
        }

# Маршруты для работы с избранными животными

@router.post("/favorites/", response_model=FavoriteAnimalResponse)
async def add_to_favorites(
    favorite: FavoriteAnimalCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Добавление животного в избранное
    
    Args:
        favorite: Данные о избранном животном
        db: Сессия базы данных
        current_user: Текущий пользователь
        
    Returns:
        FavoriteAnimalResponse: Добавленное избранное животное
    """
    # Проверяем существование животного
    animal = db.query(Animal).filter(Animal.id == favorite.animal_id).first()
    if animal is None:
        raise HTTPException(status_code=404, detail="Животное не найдено")
    
    # Проверяем, не добавлено ли уже это животное в избранное
    existing = db.query(FavoriteAnimal).filter(
        FavoriteAnimal.user_id == current_user.id,
        FavoriteAnimal.animal_id == favorite.animal_id
    ).first()
    
    if existing:
        return existing
    
    # Создаем новую запись в избранном
    new_favorite = FavoriteAnimal(user_id=current_user.id, animal_id=favorite.animal_id)
    
    try:
        db.add(new_favorite)
        db.commit()
        db.refresh(new_favorite)
        return new_favorite
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при добавлении в избранное: {str(e)}")

@router.get("/favorites/", response_model=List[AnimalDetailResponse])
async def get_favorite_animals(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Получение списка избранных животных пользователя
    
    Args:
        db: Сессия базы данных
        current_user: Текущий пользователь
        
    Returns:
        List[AnimalDetailResponse]: Список избранных животных
    """
    favorites = db.query(FavoriteAnimal).filter(FavoriteAnimal.user_id == current_user.id).all()
    animal_ids = [fav.animal_id for fav in favorites]
    
    animals = db.query(Animal).filter(Animal.id.in_(animal_ids)).all()
    return animals

@router.delete("/favorites/{animal_id}")
async def remove_from_favorites(
    animal_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Удаление животного из избранного
    
    Args:
        animal_id: ID животного
        db: Сессия базы данных
        current_user: Текущий пользователь
        
    Returns:
        dict: Сообщение об успешном удалении
    """
    favorite = db.query(FavoriteAnimal).filter(
        FavoriteAnimal.user_id == current_user.id,
        FavoriteAnimal.animal_id == animal_id
    ).first()
    
    if favorite is None:
        raise HTTPException(status_code=404, detail="Животное не найдено в избранном")
    
    try:
        db.delete(favorite)
        db.commit()
        return {"message": "Животное успешно удалено из избранного"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении из избранного: {str(e)}")

@router.get("/check-favorite/{animal_id}", response_model=bool)
async def check_is_favorite(
    animal_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Проверка, добавлено ли животное в избранное текущим пользователем
    
    Args:
        animal_id: ID животного
        db: Сессия базы данных
        current_user: Текущий пользователь
        
    Returns:
        bool: True, если животное в избранном, иначе False
    """
    favorite = db.query(FavoriteAnimal).filter(
        FavoriteAnimal.user_id == current_user.id,
        FavoriteAnimal.animal_id == animal_id
    ).first()
    
    return favorite is not None