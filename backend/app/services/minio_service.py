import io
import os
import tempfile
import shutil
from pathlib import Path
from minio import Minio
from minio.error import S3Error

# Получаем данные подключения к S3 из переменных окружения
# Изменяем переменные для внешнего S3-хранилища вместо локального MinIO
S3_INTERNAL_ENDPOINT = os.getenv("S3_INTERNAL_ENDPOINT")
S3_EXTERNAL_ENDPOINT = os.getenv("S3_EXTERNAL_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_USE_SSL = os.getenv("S3_USE_SSL").lower()

# Константы для хранилища
BUCKET_NAME = S3_BUCKET_NAME

# Инициализация клиента S3
# Используем внутренний эндпоинт для доступа из контейнеров
minio_client = Minio(
    S3_INTERNAL_ENDPOINT,
    access_key=S3_ACCESS_KEY,
    secret_key=S3_SECRET_KEY,
    secure=S3_USE_SSL  # Используем SSL для безопасного соединения
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
            # Попытка создать бакет (может потребоваться соответствующее разрешение)
            minio_client.make_bucket(bucket_name)
            print(f"Создан новый бакет: {bucket_name}")
    except S3Error as e:
        # Если бакет уже существует и создан другим пользователем, это нормально
        if "BucketAlreadyOwnedByYou" in str(e) or "BucketAlreadyExists" in str(e):
            print(f"Бакет {bucket_name} уже существует и доступен")
            return
        raise Exception(f"Ошибка при создании/проверке бакета: {e}")

def upload_file(bucket_name: str, file_obj, file_name: str, content_type: str):
    """
    Загрузить файл в S3-хранилище
    
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
        
        # Загрузить файл в S3
        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=file_name,
            data=io.BytesIO(file_data),
            length=file_size,
            content_type=content_type
        )
        
        # Формируем публичный URL для доступа к файлу
        # Используем внешний эндпоинт для публичных ссылок
        # Примечание: может потребоваться настройка CORS на S3 для доступа к файлам
        public_url = f"https://{S3_EXTERNAL_ENDPOINT}/{bucket_name}/{file_name}"
        
        return {
            "bucket_name": bucket_name,
            "file_name": file_name,
            "size": file_size,
            "content_type": content_type,
            "url": public_url
        }
    except S3Error as e:
        raise Exception(f"Ошибка при загрузке файла в S3: {e}")

def get_file(bucket_name: str, file_name: str):
    """
    Получить файл из S3-хранилища
    
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
        raise Exception(f"Ошибка при получении файла из S3: {e}")

def delete_file(bucket_name: str, file_name: str):
    """
    Удалить файл из S3-хранилища
    
    Args:
        bucket_name (str): Имя бакета
        file_name (str): Имя файла
        
    Returns:
        bool: True, если файл успешно удален
        
    Raises:
        Exception: При ошибке удаления файла
    """
    try:
        # Проверяем существование бакета
        if not minio_client.bucket_exists(bucket_name):
            print(f"Бакет {bucket_name} не существует")
            return False
            
        # Проверяем существование файла
        try:
            minio_client.stat_object(bucket_name, file_name)
        except S3Error as e:
            if "code: NoSuchKey" in str(e) or "Object does not exist" in str(e):
                print(f"Файл {file_name} не найден в бакете {bucket_name}")
                return False
            # Пробрасываем остальные ошибки
            raise
            
        # Удаляем файл
        minio_client.remove_object(bucket_name, file_name)
        print(f"Файл {file_name} успешно удален из бакета {bucket_name}")
        return True
    except S3Error as e:
        print(f"Ошибка S3 при удалении файла {file_name}: {str(e)}")
        raise Exception(f"Ошибка при удалении файла из S3: {e}")
    except Exception as e:
        print(f"Непредвиденная ошибка при удалении файла {file_name}: {str(e)}")
        raise Exception(f"Непредвиденная ошибка при удалении файла: {str(e)}")

async def delete_files_by_ids(file_ids: list, bucket_name: str = BUCKET_NAME) -> dict:
    """
    Удаляет группу файлов из S3-хранилища по их идентификаторам или полным путям
    
    Args:
        file_ids (list): Список идентификаторов файлов или полных путей для удаления
        bucket_name (str, optional): Имя бакета. По умолчанию используется BUCKET_NAME.
        
    Returns:
        dict: Отчет о результатах удаления (количество успешных/неудачных удалений)
        
    Raises:
        Exception: При критической ошибке процесса удаления
    """
    if not file_ids:
        print("Нет файлов для удаления")
        return {"success": 0, "failed": 0, "message": "Нет файлов для удаления"}
    
    # Проверяем наличие бакета
    try:
        if not minio_client.bucket_exists(bucket_name):
            print(f"Бакет {bucket_name} не существует")
            return {
                "success": 0, 
                "failed": len(file_ids), 
                "message": f"Бакет {bucket_name} не существует",
                "failed_ids": file_ids
            }
    except Exception as e:
        print(f"Ошибка при проверке существования бакета {bucket_name}: {str(e)}")
        return {
            "success": 0, 
            "failed": len(file_ids), 
            "message": f"Ошибка при проверке существования бакета: {str(e)}",
            "failed_ids": file_ids
        }
    
    success_count = 0
    failed_count = 0
    failed_ids = []
    success_ids = []
    
    print(f"Начинаем удаление {len(file_ids)} файлов из бакета {bucket_name}")
    
    # Перебираем все ID файлов и пытаемся их удалить
    for file_id in file_ids:
        if not file_id:
            print("Пропускаем пустой идентификатор файла")
            continue
            
        try:
            # Проверяем существование объекта в S3
            object_name = file_id  # Может быть как просто ID, так и полный путь (category/id.ext)
            
            try:
                minio_client.stat_object(bucket_name, object_name)
                exists = True
                print(f"Объект '{object_name}' найден в бакете {bucket_name}")
            except S3Error as se:
                if "code: NoSuchKey" in str(se) or "Object does not exist" in str(se):
                    exists = False
                    print(f"Объект '{object_name}' не найден в бакете {bucket_name}")
                else:
                    # Пробрасываем другие S3 ошибки
                    raise
            
            # Если файл существует, удаляем его
            if exists:
                minio_client.remove_object(bucket_name, object_name)
                print(f"Объект '{object_name}' успешно удален из бакета {bucket_name}")
                success_count += 1
                success_ids.append(object_name)
            else:
                failed_count += 1
                failed_ids.append(object_name)
                print(f"Не удалось удалить объект '{object_name}': файл не существует в бакете")
                
        except Exception as e:
            failed_count += 1
            failed_ids.append(file_id)
            print(f"Ошибка при удалении объекта '{file_id}': {str(e)}")
    
    result = {
        "success": success_count,
        "failed": failed_count,
        "message": f"Удалено {success_count} из {len(file_ids)} файлов"
    }
    
    if success_count > 0:
        result["success_ids"] = success_ids
    
    if failed_count > 0:
        result["failed_ids"] = failed_ids
        
    print(f"Результат удаления файлов: {result}")
    return result

async def upload_file_to_minio(file_path: str, object_name: str, bucket_name: str = BUCKET_NAME) -> bool:
    """
    Загружает файл в S3-хранилище с локальной файловой системы
    
    Args:
        file_path (str): Путь к локальному файлу
        object_name (str): Имя объекта в хранилище (например, 'images/file.jpg')
        bucket_name (str, optional): Имя бакета. По умолчанию используется BUCKET_NAME.
        
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
        
        # Загружаем файл в S3
        minio_client.fput_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=file_path,
            content_type=content_type,
        )
        
        return True
    except S3Error as e:
        raise Exception(f"Ошибка при загрузке файла в S3: {e}")
    except Exception as e:
        raise Exception(f"Ошибка при загрузке файла: {str(e)}")

async def get_file_from_minio(object_name: str, bucket_name: str = BUCKET_NAME) -> str:
    """
    Получает файл из S3-хранилища и сохраняет во временный файл
    
    Args:
        object_name (str): Имя объекта в хранилище
        bucket_name (str, optional): Имя бакета. По умолчанию используется BUCKET_NAME.
        
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
        
        # Скачиваем файл из S3
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
        raise Exception(f"Ошибка при получении файла из S3: {e}")
    except Exception as e:
        # Удаляем временный файл в случае ошибки
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise Exception(f"Ошибка при получении файла: {str(e)}")