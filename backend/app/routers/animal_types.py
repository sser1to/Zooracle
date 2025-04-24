from fastapi import APIRouter, Depends, HTTPException # type: ignore
from sqlalchemy.orm import Session # type: ignore
from typing import List
from sqlalchemy.exc import SQLAlchemyError # type: ignore

from ..database import get_db
from ..models import AnimalType
from ..schemas import AnimalTypeCreate, AnimalTypeResponse
from ..services.auth_service import get_current_admin_user

router = APIRouter()

@router.post("/", response_model=AnimalTypeResponse)
async def create_animal_type(
    animal_type: AnimalTypeCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Создание нового типа животного (только для администраторов)
    
    Args:
        animal_type: Данные о типе животного
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        AnimalTypeResponse: Созданный тип животного
    """
    # Проверка на дубликаты
    existing = db.query(AnimalType).filter(AnimalType.name == animal_type.name).first()
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Тип животного с таким названием уже существует"
        )
    
    try:
        new_animal_type = AnimalType(**animal_type.dict())
        db.add(new_animal_type)
        db.commit()
        db.refresh(new_animal_type)
        return new_animal_type
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании типа животного: {str(e)}")

@router.get("/", response_model=List[AnimalTypeResponse])
async def get_animal_types(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Получение списка типов животных
    
    Args:
        skip: Сколько записей пропустить
        limit: Максимальное количество записей
        db: Сессия базы данных
        
    Returns:
        List[AnimalTypeResponse]: Список типов животных
    """
    animal_types = db.query(AnimalType).offset(skip).limit(limit).all()
    return animal_types

@router.get("/{animal_type_id}", response_model=AnimalTypeResponse)
async def get_animal_type(
    animal_type_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение информации о конкретном типе животного
    
    Args:
        animal_type_id: ID типа животного
        db: Сессия базы данных
        
    Returns:
        AnimalTypeResponse: Данные о типе животного
    """
    animal_type = db.query(AnimalType).filter(AnimalType.id == animal_type_id).first()
    if animal_type is None:
        raise HTTPException(status_code=404, detail="Тип животного не найден")
    return animal_type

@router.put("/{animal_type_id}", response_model=AnimalTypeResponse)
async def update_animal_type(
    animal_type_id: int,
    animal_type: AnimalTypeCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Обновление информации о типе животного (только для администраторов)
    
    Args:
        animal_type_id: ID типа животного
        animal_type: Новые данные о типе животного
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        AnimalTypeResponse: Обновленный тип животного
    """
    db_animal_type = db.query(AnimalType).filter(AnimalType.id == animal_type_id).first()
    if db_animal_type is None:
        raise HTTPException(status_code=404, detail="Тип животного не найден")
    
    # Проверка на дубликаты при обновлении
    if animal_type.name != db_animal_type.name:
        existing = db.query(AnimalType).filter(AnimalType.name == animal_type.name).first()
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Тип животного с таким названием уже существует"
            )
    
    # Обновляем атрибуты типа животного
    for key, value in animal_type.dict().items():
        setattr(db_animal_type, key, value)
    
    try:
        db.commit()
        db.refresh(db_animal_type)
        return db_animal_type
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении типа животного: {str(e)}")

@router.delete("/{animal_type_id}")
async def delete_animal_type(
    animal_type_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Удаление типа животного (только для администраторов)
    
    Args:
        animal_type_id: ID типа животного
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        dict: Сообщение об успешном удалении
    """
    db_animal_type = db.query(AnimalType).filter(AnimalType.id == animal_type_id).first()
    if db_animal_type is None:
        raise HTTPException(status_code=404, detail="Тип животного не найден")
    
    try:
        db.delete(db_animal_type)
        db.commit()
        return {"message": "Тип животного успешно удален"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении типа животного: {str(e)}")