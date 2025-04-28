from fastapi import APIRouter, Depends, HTTPException, Query # type: ignore
from sqlalchemy.orm import Session # type: ignore
from typing import List, Optional, Literal
from sqlalchemy.exc import SQLAlchemyError # type: ignore
from sqlalchemy import or_, desc, asc # type: ignore

from ..database import get_db
from ..models import Animal, AnimalPhoto, AnimalType, Habitat, FavoriteAnimal, User
from ..schemas import (
    AnimalCreate, 
    AnimalResponse, 
    AnimalDetailResponse,
    AnimalPhotoCreate,
    AnimalPhotoResponse,
    FavoriteAnimalCreate,
    FavoriteAnimalResponse
)
from ..services.auth_service import get_current_user, get_current_admin_user

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
    limit: int = 10000,  # Увеличиваем лимит до большого значения, чтобы показывать все записи
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
        # Используем оператор ilike для регистро-независимого поиска подстроки
        query = query.filter(Animal.name.ilike(f"%{search}%"))
    
    # Применяем фильтры, если они указаны
    if animal_type_id:
        query = query.filter(Animal.animal_type_id == animal_type_id)
    if habitat_id:
        query = query.filter(Animal.habitat_id == habitat_id)
    
    # Фильтруем по избранным, если запрошено и пользователь авторизован
    if favorites_only and current_user:
        # Подзапрос для получения ID избранных животных пользователя
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
    animal: AnimalCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Обновление информации о животном (только для администраторов)
    
    Args:
        animal_id: ID животного
        animal: Новые данные о животном
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        AnimalResponse: Обновленное животное
    """
    db_animal = db.query(Animal).filter(Animal.id == animal_id).first()
    if db_animal is None:
        raise HTTPException(status_code=404, detail="Животное не найдено")
    
    # Обновляем атрибуты животного
    for key, value in animal.dict().items():
        setattr(db_animal, key, value)
    
    try:
        db.commit()
        db.refresh(db_animal)
        return db_animal
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении животного: {str(e)}")

@router.delete("/{animal_id}")
async def delete_animal(
    animal_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Удаление животного (только для администраторов)
    
    Args:
        animal_id: ID животного
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        dict: Сообщение об успешном удалении
    """
    db_animal = db.query(Animal).filter(Animal.id == animal_id).first()
    if db_animal is None:
        raise HTTPException(status_code=404, detail="Животное не найдено")
    
    try:
        db.delete(db_animal)
        db.commit()
        return {"message": "Животное успешно удалено"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении животного: {str(e)}")

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
    photo_id: str,  # Изменяем тип на str для поддержки UUID 
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
    # Ищем фото по photo_id (строка) вместо id (число)
    photo = db.query(AnimalPhoto).filter(
        AnimalPhoto.photo_id == photo_id, 
        AnimalPhoto.animal_id == animal_id
    ).first()
    
    if photo is None:
        raise HTTPException(status_code=404, detail="Фото не найдено")
    
    try:
        db.delete(photo)
        db.commit()
        return {"message": "Фото успешно удалено"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении фото: {str(e)}")

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