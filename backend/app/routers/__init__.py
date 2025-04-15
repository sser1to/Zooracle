from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserResponse
from ..services import minio_service

router = APIRouter()

@router.get("/users/", response_model=List[UserResponse])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """Загрузка файла в MinIO"""
    bucket_name = "uploads"
    try:
        result = minio_service.upload_file(
            bucket_name=bucket_name,
            file_obj=file.file,
            file_name=file.filename,
            content_type=file.content_type
        )
        return {"url": f"/files/{bucket_name}/{file.filename}", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Добавьте здесь другие маршруты API