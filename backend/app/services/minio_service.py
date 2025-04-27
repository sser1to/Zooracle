import io
import os
import tempfile
import shutil
from pathlib import Path
from minio import Minio
from minio.error import S3Error

# Получаем данные подключения к MinIO из переменных окружения
MINIO_HOST = os.getenv("MINIO_HOST", "minio")  # Оставляем хост и порт, так как они фиксированы в контейнере
MINIO_PORT = os.getenv("MINIO_PORT", "9000")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")

# Константы для хранилища
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "zooracle")

# Инициализация клиента MinIO
minio_client = Minio(
    f"{MINIO_HOST}:{MINIO_PORT}",
    access_key=MINIO_ROOT_USER,
    secret_key=MINIO_ROOT_PASSWORD,
    secure=False  # Установите True для HTTPS
)

def ensure_bucket_exists(bucket_name: str):
    """
    Убедиться, что бакет существует или создать его
    
    Args:
        bucket_name (str): Имя бакета
        
    Raises:
        Exception: При ошибке создания бакета
    """
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
    except S3Error as e:
        raise Exception(f"Ошибка при создании бакета: {e}")

def upload_file(bucket_name: str, file_obj, file_name: str, content_type: str):
    """
    Загрузить файл в MinIO
    
    Args:
        bucket_name (str): Имя бакета
        file_obj: Объект файла
        file_name (str): Имя файла
        content_type (str): MIME-тип файла
        
    Returns:
        dict: Информация о загруженном файле
        
    Raises:
        Exception: При ошибке загрузки файла
    """
    try:
        ensure_bucket_exists(bucket_name)
        file_data = file_obj.read()
        file_size = len(file_data)
        
        # Загрузить файл в MinIO
        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=file_name,
            data=io.BytesIO(file_data),
            length=file_size,
            content_type=content_type
        )
        
        return {
            "bucket_name": bucket_name,
            "file_name": file_name,
            "size": file_size,
            "content_type": content_type
        }
    except S3Error as e:
        raise Exception(f"Ошибка при загрузке файла в MinIO: {e}")

def get_file(bucket_name: str, file_name: str):
    """
    Получить файл из MinIO
    
    Args:
        bucket_name (str): Имя бакета
        file_name (str): Имя файла
        
    Returns:
        bytes: Содержимое файла
        
    Raises:
        Exception: При ошибке получения файла
    """
    try:
        response = minio_client.get_object(bucket_name, file_name)
        return response.data
    except S3Error as e:
        raise Exception(f"Ошибка при получении файла из MinIO: {e}")

def delete_file(bucket_name: str, file_name: str):
    """
    Удалить файл из MinIO
    
    Args:
        bucket_name (str): Имя бакета
        file_name (str): Имя файла
        
    Returns:
        bool: True, если файл успешно удален
        
    Raises:
        Exception: При ошибке удаления файла
    """
    try:
        minio_client.remove_object(bucket_name, file_name)
        return True
    except S3Error as e:
        raise Exception(f"Ошибка при удалении файла из MinIO: {e}")

async def upload_file_to_minio(file_path: str, object_name: str, bucket_name: str = MINIO_BUCKET_NAME) -> bool:
    """
    Загружает файл в хранилище MinIO с локальной файловой системы
    
    Args:
        file_path (str): Путь к локальному файлу
        object_name (str): Имя объекта в хранилище (например, 'images/file.jpg')
        bucket_name (str, optional): Имя бакета. По умолчанию используется MINIO_BUCKET_NAME.
        
    Returns:
        bool: True, если загрузка успешна
        
    Raises:
        Exception: При ошибке загрузки файла
    """
    try:
        # Проверяем существование бакета или создаем его
        ensure_bucket_exists(bucket_name)
        
        # Получаем размер файла и тип контента
        file_size = os.path.getsize(file_path)
        
        # Определяем тип контента на основе расширения файла
        content_type = "application/octet-stream"  # По умолчанию
        ext = os.path.splitext(file_path)[1].lower()
        
        # Таблица соответствия расширений и MIME-типов
        content_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".mp4": "video/mp4",
            ".avi": "video/x-msvideo",
        }
        
        content_type = content_types.get(ext, content_type)
        
        # Загружаем файл в MinIO
        minio_client.fput_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=file_path,
            content_type=content_type,
        )
        
        return True
    except S3Error as e:
        raise Exception(f"Ошибка при загрузке файла в MinIO: {e}")
    except Exception as e:
        raise Exception(f"Ошибка при загрузке файла: {str(e)}")

async def get_file_from_minio(object_name: str, bucket_name: str = MINIO_BUCKET_NAME) -> str:
    """
    Получает файл из хранилища MinIO и сохраняет во временный файл
    
    Args:
        object_name (str): Имя объекта в хранилище
        bucket_name (str, optional): Имя бакета. По умолчанию используется MINIO_BUCKET_NAME.
        
    Returns:
        str: Путь к временному файлу
        
    Raises:
        Exception: При ошибке получения файла
    """
    try:
        # Создаем временный файл
        file_extension = os.path.splitext(object_name)[1]
        temp_file = tempfile.NamedTemporaryFile(suffix=file_extension, delete=False)
        temp_file_path = temp_file.name
        temp_file.close()
        
        # Скачиваем файл из MinIO
        minio_client.fget_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=temp_file_path
        )
        
        return temp_file_path
    except S3Error as e:
        # Если файл не найден, мы возвращаем None вместо исключения
        if "code: NoSuchKey" in str(e):
            return None
        # Для других ошибок вызываем исключение
        raise Exception(f"Ошибка при получении файла из MinIO: {e}")
    except Exception as e:
        # Удаляем временный файл в случае ошибки
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise Exception(f"Ошибка при получении файла: {str(e)}")