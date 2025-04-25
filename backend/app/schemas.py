from pydantic import BaseModel, EmailStr, Field # type: ignore
from typing import Optional, List
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


# Схемы для пользователей
class UserBase(BaseModel):
    login: str
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str  # принимает логин или email
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
    animal_id: int


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


class TestQuestionResponse(TestQuestionBase):
    id: int

    class Config:
        orm_mode = True


# Схемы для результатов тестов
class TestScoreBase(BaseModel):
    user_id: int
    test_id: int
    score: int
    date: datetime


class TestScoreCreate(BaseModel):
    test_id: int
    score: int


class TestScoreResponse(TestScoreBase):
    id: int

    class Config:
        orm_mode = True


# Схемы для животных
class AnimalBase(BaseModel):
    name: str
    animal_type_id: Optional[int] = None
    habitat_id: Optional[int] = None
    description: str
    preview_id: Optional[str] = None
    video_id: Optional[str] = None
    test_id: Optional[int] = None


class AnimalCreate(AnimalBase):
    pass


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