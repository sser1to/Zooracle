from sqlalchemy import create_engine, text, inspect # type: ignore
from sqlalchemy.ext.declarative import declarative_base # type: ignore
from sqlalchemy.orm import sessionmaker # type: ignore
import os
import traceback

# Получаем данные подключения из переменных окружения
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")  # Пароль по умолчанию
POSTGRES_HOST = os.getenv("POSTGRES_HOST")  # Значение по умолчанию для контейнера
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

# Формируем URL подключения к базе данных
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Выводим информацию о подключении (без пароля для безопасности)
print(f"Подключение к БД PostgreSQL: {POSTGRES_USER}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")

try:
    # Создаем движок SQLAlchemy с улучшенными настройками
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Проверка соединения перед использованием
        pool_recycle=3600,   # Пересоздание соединений каждый час
        connect_args={"connect_timeout": 10}  # Таймаут соединения 10 сек
    )
    
    # Проверяем соединение с БД
    print("Проверка соединения с базой данных...")
    connection = engine.connect()
    connection.close()
    print("Соединение с базой данных успешно установлено")
    
except Exception as e:
    print(f"ОШИБКА подключения к базе данных: {str(e)}")
    print("Подробная информация об ошибке:")
    traceback.print_exc()
    
    # В случае ошибки подключения к основной БД,
    # используем резервный вариант (SQLite в памяти)
    print("Использование резервной базы данных SQLite в памяти")
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для всех моделей
Base = declarative_base()

# Функция для создания всех таблиц в БД, если они не существуют
def init_db():
    """
    Создает все таблицы в базе данных на основе определенных моделей.
    
    Вызывается один раз при старте приложения, чтобы гарантировать 
    наличие всех необходимых таблиц в БД.
    
    Примечание:
        В продакшене лучше использовать миграции (Alembic) вместо 
        автоматического создания таблиц.
    """
    try:
        print("Инициализация структуры базы данных...")
        
        # Импортируем модели здесь, чтобы избежать циклических импортов
        # Импорт в функции вместо глобального уровня помогает избежать циклических зависимостей
        from .models import User, AnimalType, Animal, Habitat, AnimalPhoto
        from .models import Test, Question, QuestionType, AnswerOption
        from .models import QuestionAnswer, TestQuestion, TestScore, FavoriteAnimal
        
        # Создаем все таблицы
        print("Создание таблиц, если они не существуют...")
        Base.metadata.create_all(bind=engine)
        
        # Проверяем наличие таблиц
        # Используем инспектор SQLAlchemy правильно
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Текущие таблицы в БД: {', '.join(tables)}")
        print("Структура базы данных успешно инициализирована")
        
    except Exception as e:
        print(f"ОШИБКА при инициализации базы данных: {str(e)}")
        traceback.print_exc()
        raise

def get_db():
    """
    Функция-генератор для получения сессии базы данных.
    Используется как зависимость в FastAPI для предоставления сессии в запросах.
    
    Yields:
        Session: Сессия базы данных
        
    Примечание:
        Функция автоматически закрывает сессию после использования
        и обрабатывает возможные исключения.
    """
    db = SessionLocal()
    try:
        # Используем функцию text() для явного обозначения SQL-запроса
        # В SQLAlchemy 2.0+ требуется явно оборачивать текстовые запросы в text()
        db.execute(text("SELECT 1"))
        print("Сессия БД успешно создана")
        yield db
    except Exception as e:
        print(f"ОШИБКА при работе с сессией БД: {str(e)}")
        raise  # Пробрасываем исключение для обработки на уровне маршрутизатора
    finally:
        print("Закрытие сессии БД")
        db.close()