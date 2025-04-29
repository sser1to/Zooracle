from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float, Text # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from datetime import datetime, timedelta
import secrets

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    login = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    password = Column(Text, nullable=False)
    is_admin = Column(Boolean, nullable=False)

    favorite_animals = relationship("FavoriteAnimal", back_populates="user")
    test_scores = relationship("TestScore", back_populates="user")
    reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")


class AnimalPhoto(Base):
    __tablename__ = "animal_photos"

    id = Column(Integer, primary_key=True)
    animal_id = Column(Integer, ForeignKey("animals.id"), nullable=False)
    photo_id = Column(Text, nullable=False)

    animal = relationship("Animal", back_populates="photos")


class AnimalType(Base):
    __tablename__ = "animal_types"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)

    animals = relationship("Animal", back_populates="animal_type")


class Animal(Base):
    __tablename__ = "animals"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    animal_type_id = Column(Integer, ForeignKey("animal_types.id"))
    habitat_id = Column(Integer, ForeignKey("habitats.id"))
    description = Column(Text, nullable=False)
    preview_id = Column(Text)
    video_id = Column(Text)
    test_id = Column(Integer, ForeignKey("tests.id"))

    animal_type = relationship("AnimalType", back_populates="animals")
    habitat = relationship("Habitat", back_populates="animals")
    test = relationship("Test", back_populates="animals")
    # Добавляем cascade="all, delete-orphan" для автоматического удаления связанных фотографий
    photos = relationship("AnimalPhoto", back_populates="animal", cascade="all, delete-orphan")
    # Также добавляем cascade для избранных животных
    favorite_animals = relationship("FavoriteAnimal", back_populates="animal", cascade="all, delete-orphan")


class AnswerOption(Base):
    __tablename__ = "answer_options"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)

    question_answers = relationship("QuestionAnswer", back_populates="answer")


class FavoriteAnimal(Base):
    __tablename__ = "favorite_animals"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    animal_id = Column(Integer, ForeignKey("animals.id"))

    user = relationship("User", back_populates="favorite_animals")
    animal = relationship("Animal", back_populates="favorite_animals")


class Habitat(Base):
    __tablename__ = "habitats"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)

    animals = relationship("Animal", back_populates="habitat")


class QuestionAnswer(Base):
    __tablename__ = "question_answer"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    answer_id = Column(Integer, ForeignKey("answer_options.id"))

    question = relationship("Question", back_populates="question_answers")
    answer = relationship("AnswerOption", back_populates="question_answers")


class QuestionType(Base):
    __tablename__ = "question_types"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)

    questions = relationship("Question", back_populates="question_type")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    question_type_id = Column(Integer, ForeignKey("question_types.id"))

    question_type = relationship("QuestionType", back_populates="questions")
    question_answers = relationship("QuestionAnswer", back_populates="question")
    test_questions = relationship("TestQuestion", back_populates="question")


class TestScore(Base):
    __tablename__ = "test_score"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    test_id = Column(Integer, ForeignKey("tests.id"))
    score = Column(Integer, nullable=False)
    date = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="test_scores")
    test = relationship("Test", back_populates="test_scores")


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)

    animals = relationship("Animal", back_populates="test")
    test_scores = relationship("TestScore", back_populates="test")
    test_questions = relationship("TestQuestion", back_populates="test")


class TestQuestion(Base):
    __tablename__ = "test_questions"

    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey("tests.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))

    test = relationship("Test", back_populates="test_questions")
    question = relationship("Question", back_populates="test_questions")


class PasswordResetToken(Base):
    """
    Модель для хранения токенов сброса пароля
    
    Attributes:
        id (int): Уникальный идентификатор токена
        token (str): Уникальный токен для сброса пароля
        user_id (int): Идентификатор пользователя, связанный с токеном
        email (str): Email пользователя в момент создания токена
        created_at (DateTime): Дата и время создания токена
        expires_at (DateTime): Дата и время истечения срока действия токена
        is_used (Boolean): Был ли токен уже использован
    """
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    
    # Связь с пользователем
    user = relationship("User", back_populates="reset_tokens")

    @classmethod
    def generate(cls, user_id, email, expires_hours=24):
        """
        Создает новый токен для сброса пароля
        
        Args:
            user_id (int): ID пользователя
            email (str): Email пользователя
            expires_hours (int, optional): Срок действия токена в часах. По умолчанию 24.
            
        Returns:
            PasswordResetToken: Объект токена для сброса пароля
        """
        token_value = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        return cls(
            token=token_value,
            user_id=user_id,
            email=email,
            expires_at=expires_at
        )
    
    def is_valid(self):
        """
        Проверяет действительность токена
        
        Returns:
            bool: True, если токен действителен (не истек срок и не использован)
        """
        return not self.is_used and datetime.utcnow() < self.expires_at
    
    def invalidate(self):
        """
        Помечает токен как использованный
        """
        self.is_used = True