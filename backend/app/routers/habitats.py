from fastapi import APIRouter, Depends, HTTPException # type: ignore
from sqlalchemy.orm import Session # type: ignore
from typing import List
from sqlalchemy.exc import SQLAlchemyError # type: ignore

from ..database import get_db
from ..models import Habitat
from ..schemas import HabitatCreate, HabitatResponse
from ..services.auth_service import get_current_admin_user

router = APIRouter()

@router.post("/", response_model=HabitatResponse)
async def create_habitat(
    habitat: HabitatCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Создание нового места обитания (только для администраторов)
    
    Args:
        habitat: Данные о месте обитания
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        HabitatResponse: Созданное место обитания
    """
    # Проверка на дубликаты
    existing = db.query(Habitat).filter(Habitat.name == habitat.name).first()
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Место обитания с таким названием уже существует"
        )
    
    try:
        new_habitat = Habitat(**habitat.dict())
        db.add(new_habitat)
        db.commit()
        db.refresh(new_habitat)
        return new_habitat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании места обитания: {str(e)}")

@router.get("/", response_model=List[HabitatResponse])
async def get_habitats(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Получение списка мест обитания
    
    Args:
        skip: Сколько записей пропустить
        limit: Максимальное количество записей
        db: Сессия базы данных
        
    Returns:
        List[HabitatResponse]: Список мест обитания
    """
    habitats = db.query(Habitat).offset(skip).limit(limit).all()
    return habitats

@router.get("/{habitat_id}", response_model=HabitatResponse)
async def get_habitat(
    habitat_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение информации о конкретном месте обитания
    
    Args:
        habitat_id: ID места обитания
        db: Сессия базы данных
        
    Returns:
        HabitatResponse: Данные о месте обитания
    """
    habitat = db.query(Habitat).filter(Habitat.id == habitat_id).first()
    if habitat is None:
        raise HTTPException(status_code=404, detail="Место обитания не найдено")
    return habitat

@router.put("/{habitat_id}", response_model=HabitatResponse)
async def update_habitat(
    habitat_id: int,
    habitat: HabitatCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Обновление информации о месте обитания (только для администраторов)
    
    Args:
        habitat_id: ID места обитания
        habitat: Новые данные о месте обитания
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        HabitatResponse: Обновленное место обитания
    """
    db_habitat = db.query(Habitat).filter(Habitat.id == habitat_id).first()
    if db_habitat is None:
        raise HTTPException(status_code=404, detail="Место обитания не найдено")
    
    # Проверка на дубликаты при обновлении
    if habitat.name != db_habitat.name:
        existing = db.query(Habitat).filter(Habitat.name == habitat.name).first()
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Место обитания с таким названием уже существует"
            )
    
    # Обновляем атрибуты места обитания
    for key, value in habitat.dict().items():
        setattr(db_habitat, key, value)
    
    try:
        db.commit()
        db.refresh(db_habitat)
        return db_habitat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении места обитания: {str(e)}")

@router.delete("/{habitat_id}")
async def delete_habitat(
    habitat_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Удаление места обитания (только для администраторов)
    
    Args:
        habitat_id: ID места обитания
        db: Сессия базы данных
        current_user: Текущий пользователь (должен быть администратором)
        
    Returns:
        dict: Сообщение об успешном удалении
    """
    db_habitat = db.query(Habitat).filter(Habitat.id == habitat_id).first()
    if db_habitat is None:
        raise HTTPException(status_code=404, detail="Место обитания не найдено")
    
    try:
        db.delete(db_habitat)
        db.commit()
        return {"message": "Место обитания успешно удалено"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении места обитания: {str(e)}")