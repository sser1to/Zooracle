from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
import uuid
from fastapi.responses import FileResponse
import os
from pathlib import Path

from ..database import get_db
from ..models import User
from ..services.auth_service import get_current_user, get_current_admin_user
from ..services.minio_service import upload_file_to_minio, get_file_from_minio

router = APIRouter()

# Путь для временного хранения файлов перед отправкой в MinIO
# Используем стандартную директорию для временных файлов /tmp вместо создания новой директории
TEMP_UPLOAD_DIR = Path("/tmp/zooracle_uploads")
TEMP_UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload/")
async def upload_media_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Загрузка медиа-файла на сервер
    
    Args:
        file: Файл для загрузки
        current_user: Текущий пользователь 
        
    Returns:
        dict: Информация о загруженном файле с его ID
    """
    try:
        # Создаем уникальный идентификатор для файла
        file_id = str(uuid.uuid4())
        
        # Получаем расширение файла
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        # Проверяем допустимые типы файлов
        allowed_image_extensions = [".jpg", ".jpeg", ".png", ".webp"]
        allowed_video_extensions = [".mp4", ".avi"]
        
        if file_extension not in allowed_image_extensions + allowed_video_extensions:
            raise HTTPException(
                status_code=400, 
                detail="Недопустимый тип файла. Разрешены только JPG, JPEG, PNG, WEBP, MP4, AVI"
            )
        
        # Временный путь для сохранения файла
        temp_file_path = TEMP_UPLOAD_DIR / f"{file_id}{file_extension}"
        
        # Сохраняем файл во временную директорию
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Категория файла (изображение или видео)
        file_category = "images" if file_extension in allowed_image_extensions else "videos"
        
        # Загружаем файл в MinIO
        object_name = f"{file_category}/{file_id}{file_extension}"
        await upload_file_to_minio(
            file_path=str(temp_file_path),
            object_name=object_name
        )
        
        # Получаем размер файла
        file_size = os.path.getsize(temp_file_path)
        
        # Удаляем временный файл
        os.remove(temp_file_path)
        
        return {
            "file_id": file_id,
            "original_filename": file.filename,
            "content_type": file.content_type,
            "file_size": file_size,
            "extension": file_extension
        }
    except Exception as e:
        # Очистка при ошибке
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Ошибка при загрузке файла: {str(e)}")

@router.get("/{file_id}")
async def get_media(
    file_id: str,
):
    """
    Получение медиа-файла по ID
    
    Args:
        file_id: ID файла
        
    Returns:
        FileResponse: Файл
    """
    try:
        # Пытаемся найти файл сначала среди изображений, потом среди видео
        for category in ["images", "videos"]:
            for ext in [".jpg", ".jpeg", ".png", ".webp", ".mp4", ".avi"]:
                object_name = f"{category}/{file_id}{ext}"
                
                try:
                    # Пробуем получить файл из MinIO
                    temp_file_path = await get_file_from_minio(object_name)
                    
                    if temp_file_path:
                        # Определяем тип содержимого
                        content_types = {
                            ".jpg": "image/jpeg",
                            ".jpeg": "image/jpeg",
                            ".png": "image/png",
                            ".webp": "image/webp",
                            ".mp4": "video/mp4",
                            ".avi": "video/x-msvideo",
                        }
                        
                        # Возвращаем файл с соответствующими заголовками
                        return FileResponse(
                            path=temp_file_path,
                            media_type=content_types.get(ext, "application/octet-stream"),
                            filename=f"{file_id}{ext}"
                        )
                except:
                    # Если файл не найден с этим расширением, пробуем следующее
                    continue
        
        # Если файл не найден
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении файла: {str(e)}")