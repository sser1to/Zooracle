from sqlalchemy import create_engine, text, inspect # type: ignore
from sqlalchemy.ext.declarative import declarative_base # type: ignore
from sqlalchemy.orm import sessionmaker # type: ignore
import os
import traceback
import psycopg2  # Библиотека для прямого подключения к PostgreSQL
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Получаем данные подключения из переменных окружения
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")  # Пароль по умолчанию
POSTGRES_HOST = os.getenv("POSTGRES_HOST")  # Значение по умолчанию для контейнера
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

# Формируем URL подключения к базе данных
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Функция для проверки существования базы данных и её создания, если нужно
def ensure_database_exists():
    """
    Проверяет существование базы данных, указанной в .env, и создаёт её,
    если она не существует.
    
    Returns:
        bool: True, если база уже существовала или была успешно создана, 
              False в случае ошибки
    """
    try:
        # Подключаемся к системной базе PostgreSQL для проверки существования БД
        system_conn = psycopg2.connect(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database='postgres'  # Стандартная БД в PostgreSQL
        )
        
        # Делаем автокоммит для DDL запросов (CREATE DATABASE)
        system_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = system_conn.cursor()
        
        # Проверяем существование базы данных
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (POSTGRES_DB,))
        exists = cursor.fetchone()
        
        # Создаем БД, если она не существует
        if not exists:
            print(f"База данных '{POSTGRES_DB}' не существует. Создание...")
            cursor.execute(f"CREATE DATABASE {POSTGRES_DB}")
            print(f"База данных '{POSTGRES_DB}' успешно создана!")
        else:
            print(f"База данных '{POSTGRES_DB}' уже существует")
        
        cursor.close()
        system_conn.close()
        return True
    except Exception as e:
        print(f"ОШИБКА при проверке/создании базы данных: {str(e)}")
        traceback.print_exc()
        return False

# Выводим информацию о подключении (без пароля для безопасности)
print(f"Подключение к БД PostgreSQL: {POSTGRES_USER}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")

try:
    # Проверяем существование БД и создаём её при необходимости
    db_exists = ensure_database_exists()
    
    # Если не удалось убедиться в существовании БД, возможно нет прав на создание
    # Всё равно пытаемся подключиться, вдруг БД уже есть
    if not db_exists:
        print("Не удалось проверить/создать базу данных. Пытаемся подключиться напрямую...")
    
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

def populate_initial_data():
    """
    Заполняет таблицы начальными данными, если они пусты.
    
    Эта функция вставляет предопределенные записи в такие таблицы как:
    - animal_types (типы животных)
    - habitats (среды обитания)
    - и другие справочники
    
    Вызывается после создания структуры БД для обеспечения наличия 
    базовых справочных данных.
    """
    try:
        print("Заполнение таблиц начальными данными...")
        db = SessionLocal()
        
        # Импортируем модели
        from .models import AnimalType, Habitat, QuestionType
        
        # Заполняем типы животных, если таблица пуста
        if db.query(AnimalType).count() == 0:
            print("Вставка начальных типов животных...")
            animal_types = [
                AnimalType(name="Млекопитающие"),
                AnimalType(name="Птицы"),
                AnimalType(name="Пресмыкающиеся"),
                AnimalType(name="Земноводные"),
                AnimalType(name="Рыбы")
            ]
            db.bulk_save_objects(animal_types)
            
            # Фиксируем изменения
            db.commit()
            print(f"Вставлено {len(animal_types)} типов животных")
        else:
            print("Таблица типов животных уже содержит данные")
        
        # Заполняем среды обитания, если таблица пуста
        if db.query(Habitat).count() == 0:
            print("Вставка начальных сред обитания...")
            habitats = [
                Habitat(name="Тундра"),
                Habitat(name="Тайга"),
                Habitat(name="Лиственные леса"),
                Habitat(name="Саванна"),
                Habitat(name="Пустыня"),
                Habitat(name="Степь"),
                Habitat(name="Тропический лес"),
                Habitat(name="Горы"),
                Habitat(name="Океан"),
                Habitat(name="Море"),
                Habitat(name="Озера"),
                Habitat(name="Реки")
            ]
            db.bulk_save_objects(habitats)
            
            # Фиксируем изменения
            db.commit()
            print(f"Вставлено {len(habitats)} сред обитания")
        else:
            print("Таблица сред обитания уже содержит данные")

        # Заполняем типы вопросов, если таблица пуста
        if db.query(QuestionType).count() == 0:
            print("Вставка начальных типов животных...")
            question_types = [
                QuestionType(name="Ввод ответов"),
                QuestionType(name="Выбор одного правильного ответа"),
                QuestionType(name="Выбор нескольких правильных ответов")
            ]
            db.bulk_save_objects(question_types)
            
            # Фиксируем изменения
            db.commit()
            print(f"Вставлено {len(question_types)} типов вопросов")
        else:
            print("Таблица типов вопросов уже содержит данные")

        db.close()
        print("Заполнение начальными данными завершено")
    except Exception as e:
        print(f"ОШИБКА при заполнении начальными данными: {str(e)}")
        traceback.print_exc()
        # Не пробрасываем исключение, так как отсутствие начальных данных
        # не является критической ошибкой для работы приложения

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
        
        # Заполняем таблицы начальными данными
        populate_initial_data()
        
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