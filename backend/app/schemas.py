from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Union
from datetime import datetime


# Схемы авторизации
class TokenData(BaseModel):
    username: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    login: str
    email: str
    is_admin: bool


# Схемы для сброса пароля
class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)


# Схемы для подтверждения email
class EmailVerificationRequest(BaseModel):
    email: EmailStr


class EmailVerificationCode(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


# Схемы для пользователей
class UserBase(BaseModel):
    login: str
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    is_admin: bool

    class Config:
        orm_mode = True


# Схемы для типов животных
class AnimalTypeBase(BaseModel):
    name: str


class AnimalTypeCreate(AnimalTypeBase):
    pass


class AnimalTypeResponse(AnimalTypeBase):
    id: int

    class Config:
        orm_mode = True


# Схемы для мест обитания
class HabitatBase(BaseModel):
    name: str


class HabitatCreate(HabitatBase):
    pass


class HabitatResponse(HabitatBase):
    id: int

    class Config:
        orm_mode = True


# Схемы для фото животных
class AnimalPhotoBase(BaseModel):
    photo_id: str


class AnimalPhotoCreate(AnimalPhotoBase):
    pass


class AnimalPhotoResponse(AnimalPhotoBase):
    id: int
    animal_id: int

    class Config:
        orm_mode = True


# Схемы для тестов
class TestBase(BaseModel):
    name: str


class TestCreate(TestBase):
    pass


class TestResponse(TestBase):
    id: int

    class Config:
        orm_mode = True


# Схемы для типов вопросов
class QuestionTypeBase(BaseModel):
    name: str


class QuestionTypeCreate(QuestionTypeBase):
    pass


class QuestionTypeResponse(QuestionTypeBase):
    id: int

    class Config:
        orm_mode = True


# Схемы для вопросов
class QuestionBase(BaseModel):
    name: str
    question_type_id: int


class QuestionCreate(QuestionBase):
    pass


class QuestionResponse(QuestionBase):
    id: int

    class Config:
        orm_mode = True


# Схемы для вариантов ответов
class AnswerOptionBase(BaseModel):
    name: str
    is_correct: bool


class AnswerOptionCreate(AnswerOptionBase):
    pass


class AnswerOptionResponse(AnswerOptionBase):
    id: int

    class Config:
        orm_mode = True


# Схемы для связи вопросов и ответов
class QuestionAnswerBase(BaseModel):
    question_id: int
    answer_id: int


class QuestionAnswerCreate(QuestionAnswerBase):
    pass


# Специальная схема для добавления ответа к вопросу
class AddAnswerToQuestionCreate(BaseModel):
    """
    Схема для добавления ответа к вопросу по ID
    
    В отличие от QuestionAnswerCreate, не требует указания question_id, 
    т.к. он передаётся в URL маршрута
    
    Attributes:
        answer_id (int): ID ответа, который нужно добавить к вопросу
    """
    answer_id: int


class QuestionAnswerResponse(QuestionAnswerBase):
    id: int

    class Config:
        orm_mode = True


# Схемы для связи тестов и вопросов
class TestQuestionBase(BaseModel):
    test_id: int
    question_id: int


class TestQuestionCreate(TestQuestionBase):
    pass


# Специальная схема для добавления вопроса к тесту
class AddQuestionToTestCreate(BaseModel):
    """
    Схема для добавления вопроса к тесту по ID
    
    В отличие от TestQuestionCreate, не требует указания test_id, 
    т.к. он передаётся в URL маршрута
    
    Attributes:
        question_id (int): ID вопроса, который нужно добавить к тесту
    """
    question_id: int


class TestQuestionResponse(TestQuestionBase):
    id: int

    class Config:
        orm_mode = True


# Схемы для результатов тестов
class TestScoreBase(BaseModel):
    """
    Базовая схема для результатов теста
    
    Attributes:
        test_id: ID теста (может быть None)
        user_id: ID пользователя
        score: Результат теста в формате "X/Y" (правильных ответов из общего числа вопросов)
        date: Дата прохождения теста
    """
    test_id: Optional[int] = None
    user_id: int
    score: str
    date: datetime


class TestScoreCreate(BaseModel):
    """
    Схема для создания результата теста
    
    Attributes:
        test_id: ID теста
        correct_answers: Количество правильных ответов
        total_questions: Общее количество вопросов
    """
    test_id: int
    correct_answers: int
    total_questions: int


class TestScore(TestScoreBase):
    """
    Схема для отображения результата теста
    
    Attributes:
        id: Уникальный идентификатор результата
    """
    id: int
    
    class Config:
        orm_mode = True


# Схемы для животных
class AnimalBase(BaseModel):
    name: Optional[str] = None
    animal_type_id: Optional[int] = None
    habitat_id: Optional[int] = None
    description: Optional[str] = None
    preview_id: Optional[str] = None
    video_id: Optional[str] = None
    test_id: Optional[int] = None


class AnimalCreate(BaseModel):
    """
    Схема для создания нового животного.
    При создании обязательно требуются имя и описание.
    """
    name: str
    animal_type_id: Optional[int] = None
    habitat_id: Optional[int] = None
    description: str
    preview_id: Optional[str] = None
    video_id: Optional[str] = None
    test_id: Optional[int] = None


class AnimalResponse(AnimalBase):
    id: int

    class Config:
        orm_mode = True


class AnimalDetailResponse(AnimalResponse):
    animal_type: Optional[AnimalTypeResponse] = None
    habitat: Optional[HabitatResponse] = None
    photos: List[AnimalPhotoResponse] = []

    class Config:
        orm_mode = True


# Схемы для избранных животных
class FavoriteAnimalBase(BaseModel):
    animal_id: int


class FavoriteAnimalCreate(FavoriteAnimalBase):
    pass


class FavoriteAnimalResponse(FavoriteAnimalBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


# Схемы для работы с AnswerOption (вариантами ответов)
class AnswerOptionBase(BaseModel):
    """
    Базовая схема для вариантов ответов
    
    Attributes:
        name: Текст варианта ответа
        is_correct: Является ли вариант правильным ответом
    """
    name: str
    is_correct: bool


class AnswerOptionCreate(AnswerOptionBase):
    """
    Схема для создания варианта ответа
    """
    id: Optional[int] = None


class AnswerOptionUpdate(AnswerOptionBase):
    """
    Схема для обновления варианта ответа
    """
    name: Optional[str] = None
    is_correct: Optional[bool] = None


class AnswerOption(AnswerOptionBase):
    """
    Схема для отображения варианта ответа
    
    Attributes:
        id: Уникальный идентификатор варианта ответа
    """
    id: int
    
    class Config:
        orm_mode = True


# Схемы для работы с Questions (вопросами)
class QuestionBase(BaseModel):
    """
    Базовая схема для вопросов
    
    Attributes:
        name: Текст вопроса
        question_type_id: ID типа вопроса (1-текст, 2-один ответ, 3-множественный выбор)
    """
    name: str
    question_type_id: int


class QuestionCreate(QuestionBase):
    """
    Схема для создания вопроса
    
    Attributes:
        answers: Список вариантов ответов для данного вопроса
    """
    id: Optional[int] = None
    answers: List[AnswerOptionCreate]


class QuestionUpdate(BaseModel):
    """
    Схема для обновления вопроса
    
    Attributes:
        name: Текст вопроса
        question_type_id: ID типа вопроса
        answers: Список вариантов ответов для данного вопроса
    """
    name: Optional[str] = None
    question_type_id: Optional[int] = None
    answers: Optional[List[AnswerOptionCreate]] = None


class Question(QuestionBase):
    """
    Схема для отображения вопроса
    
    Attributes:
        id: Уникальный идентификатор вопроса
        answers: Список вариантов ответов
    """
    id: int
    answers: List[AnswerOption] = []
    
    class Config:
        orm_mode = True


# Схемы для работы с Tests (тестами)
class TestBase(BaseModel):
    """
    Базовая схема для тестов
    
    Attributes:
        name: Название теста
    """
    name: str


class TestCreate(TestBase):
    """
    Схема для создания теста
    
    Attributes:
        animal_id: ID связанного животного (опциональное)
    """
    animal_id: Optional[int] = None


class TestUpdate(BaseModel):
    """
    Схема для обновления теста
    
    Attributes:
        name: Название теста
    """
    name: Optional[str] = None


class Test(TestBase):
    """
    Схема для отображения теста
    
    Attributes:
        id: Уникальный идентификатор теста
    """
    id: int
    
    class Config:
        orm_mode = True


class TestWithQuestions(Test):
    """
    Расширенная схема теста с вопросами
    
    Attributes:
        questions: Список вопросов, входящих в тест
    """
    questions: List[Question] = []


class TestQuestionCreate(BaseModel):
    """
    Схема для связи теста и вопроса
    
    Attributes:
        test_id: ID теста
        question_id: ID вопроса
    """
    test_id: int
    question_id: int


class TestQuestionResponse(BaseModel):
    """
    Схема для отображения связи теста и вопроса
    
    Attributes:
        id: Уникальный идентификатор связи
        test_id: ID теста
        question_id: ID вопроса
    """
    id: int
    test_id: int
    question_id: int
    
    class Config:
        orm_mode = True


class TestQuestionsUpdate(BaseModel):
    """
    Схема для обновления списка вопросов теста
    
    Attributes:
        questions: Список вопросов для обновления
    """
    questions: List[QuestionCreate]


# Схемы для типов вопросов
class QuestionTypeBase(BaseModel):
    """
    Базовая схема для типов вопросов
    
    Attributes:
        name: Название типа вопроса
    """
    name: str


class QuestionType(QuestionTypeBase):
    """
    Схема для отображения типа вопроса
    
    Attributes:
        id: Уникальный идентификатор типа вопроса
    """
    id: int
    
    class Config:
        orm_mode = True