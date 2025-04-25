import random
import string
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

# Настройка логирования
logger = logging.getLogger("email_verification_service")

# Словарь для хранения кодов верификации
# Структура: {email: (код, время_создания)}
verification_codes: Dict[str, Tuple[str, float]] = {}

# Время жизни кода верификации (в секундах)
VERIFICATION_CODE_TTL = 300  # 5 минут


def generate_verification_code(length: int = 6) -> str:
    """
    Генерирует случайный код подтверждения из цифр.
    
    Args:
        length (int): Длина кода. По умолчанию 6.
        
    Returns:
        str: Сгенерированный код подтверждения.
    """
    # Генерируем код только из цифр
    return ''.join(random.choices(string.digits, k=length))


def create_verification_code(email: str) -> str:
    """
    Создает новый код верификации для указанного email.
    
    Args:
        email (str): Email для которого создается код.
        
    Returns:
        str: Созданный код верификации.
    """
    # Удаляем старые коды для этого email, если они существуют
    if email in verification_codes:
        logger.info(f"Удаление старого кода верификации для {email}")
    
    # Генерируем новый код
    code = generate_verification_code()
    current_time = time.time()
    
    # Сохраняем код и время его создания
    verification_codes[email] = (code, current_time)
    
    logger.info(f"Создан новый код верификации для {email}: {code}")
    return code


def verify_code(email: str, code: str) -> bool:
    """
    Проверяет правильность кода верификации для указанного email.
    
    Args:
        email (str): Email для проверки.
        code (str): Код верификации для проверки.
        
    Returns:
        bool: True если код верен и не истек срок его действия, иначе False.
    """
    # Очищаем устаревшие коды
    cleanup_expired_codes()
    
    # Проверяем существование кода для email
    if email not in verification_codes:
        logger.warning(f"Код верификации для {email} не найден")
        return False
    
    stored_code, created_time = verification_codes[email]
    current_time = time.time()
    
    # Проверяем срок действия кода
    if current_time - created_time > VERIFICATION_CODE_TTL:
        logger.warning(f"Код верификации для {email} истек")
        # Удаляем истекший код
        del verification_codes[email]
        return False
    
    # Проверяем совпадение кодов
    if stored_code != code:
        logger.warning(f"Неверный код верификации для {email}")
        return False
    
    # Если все проверки пройдены, удаляем использованный код
    logger.info(f"Код верификации для {email} успешно подтвержден")
    del verification_codes[email]
    return True


def cleanup_expired_codes() -> None:
    """
    Удаляет все истекшие коды верификации.
    """
    current_time = time.time()
    expired_emails = []
    
    # Находим все истекшие коды
    for email, (code, created_time) in verification_codes.items():
        if current_time - created_time > VERIFICATION_CODE_TTL:
            expired_emails.append(email)
    
    # Удаляем истекшие коды
    for email in expired_emails:
        del verification_codes[email]
        logger.info(f"Удален истекший код верификации для {email}")


def get_verification_code(email: str) -> Optional[str]:
    """
    Получает текущий код верификации для email.
    
    Args:
        email (str): Email для которого нужно получить код.
        
    Returns:
        Optional[str]: Код верификации или None, если код не существует или истек.
    """
    cleanup_expired_codes()
    
    if email not in verification_codes:
        return None
    
    code, _ = verification_codes[email]
    return code