import time
import logging
from typing import Dict, Tuple, Optional

# Настройка логирования
logger = logging.getLogger("user_registration_service")

# Структура для хранения временных данных пользователей
pending_users: Dict[str, Tuple[dict, float]] = {}

# Время жизни данных пользователя
PENDING_USER_TTL = 3600  # 1 час


def store_pending_user(email: str, user_data: dict) -> None:
    """
    Временно сохраняет данные пользователя для последующей регистрации
    после подтверждения email.
    
    Args:
        email (str): Email пользователя
        user_data (dict): Данные пользователя для регистрации
    """
    # Удаляем предыдущие данные для этого email, если они существуют
    if email in pending_users:
        logger.info(f"Обновление временных данных пользователя для {email}")
    
    # Сохраняем данные пользователя и время создания
    current_time = time.time()
    pending_users[email] = (user_data, current_time)
    
    logger.info(f"Сохранены временные данные пользователя для {email}")
    
    # Очистка устаревших данных
    cleanup_expired_pending_users()


def get_pending_user(email: str) -> Optional[dict]:
    """
    Получает временно сохраненные данные пользователя по email.
    
    Args:
        email (str): Email пользователя
        
    Returns:
        Optional[dict]: Данные пользователя или None, если не найдены или истек срок
    """
    # Очистка устаревших данных
    cleanup_expired_pending_users()
    
    if email not in pending_users:
        logger.warning(f"Временные данные пользователя не найдены для {email}")
        return None
    
    user_data, created_time = pending_users[email]
    current_time = time.time()
    
    # Проверяем срок действия
    if current_time - created_time > PENDING_USER_TTL:
        logger.warning(f"Истек срок действия временных данных пользователя для {email}")
        # Удаляем истекшие данные
        del pending_users[email]
        return None
    
    return user_data


def remove_pending_user(email: str) -> bool:
    """
    Удаляет временные данные пользователя.
    
    Args:
        email (str): Email пользователя
        
    Returns:
        bool: True при успешном удалении, False если данные не найдены
    """
    if email in pending_users:
        del pending_users[email]
        logger.info(f"Удалены временные данные пользователя для {email}")
        return True
        
    logger.warning(f"Попытка удаления несуществующих временных данных пользователя для {email}")
    return False


def cleanup_expired_pending_users() -> None:
    """
    Удаляет все записи временного хранилища пользователей,
    срок действия которых истек.
    """
    current_time = time.time()
    expired_emails = []
    
    # Находим все истекшие данные
    for email, (_, created_time) in pending_users.items():
        if current_time - created_time > PENDING_USER_TTL:
            expired_emails.append(email)
    
    # Удаляем истекшие данные
    for email in expired_emails:
        del pending_users[email]
        logger.info(f"Удалены истекшие временные данные пользователя для {email}")