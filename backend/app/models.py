from sqlalchemy import Column, Integer, Text, Boolean, DateTime, ForeignKey # type: ignore
from sqlalchemy.orm import relationship # type: ignore
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
    photos = relationship("AnimalPhoto", back_populates="animal")
    favorite_animals = relationship("FavoriteAnimal", back_populates="animal")

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