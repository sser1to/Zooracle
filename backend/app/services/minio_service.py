import io
import os
from minio import Minio
from minio.error import S3Error

# Получаем данные подключения к MinIO из переменных окружения
MINIO_HOST = os.getenv("MINIO_HOST", "minio")  # Оставляем хост и порт, так как они фиксированы в контейнере
MINIO_PORT = os.getenv("MINIO_PORT", "9000")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")

minio_client = Minio(
    f"{MINIO_HOST}:{MINIO_PORT}",
    access_key=MINIO_ROOT_USER,
    secret_key=MINIO_ROOT_PASSWORD,
    secure=False  # Установите True для HTTPS
)

def ensure_bucket_exists(bucket_name: str):
    """Убедиться, что бакет существует или создать его"""
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
    except S3Error as e:
        raise Exception(f"Ошибка при создании бакета: {e}")

def upload_file(bucket_name: str, file_obj, file_name: str, content_type: str):
    """Загрузить файл в MinIO"""
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
    """Получить файл из MinIO"""
    try:
        response = minio_client.get_object(bucket_name, file_name)
        return response.data
    except S3Error as e:
        raise Exception(f"Ошибка при получении файла из MinIO: {e}")

def delete_file(bucket_name: str, file_name: str):
    """Удалить файл из MinIO"""
    try:
        minio_client.remove_object(bucket_name, file_name)
        return True
    except S3Error as e:
        raise Exception(f"Ошибка при удалении файла из MinIO: {e}")