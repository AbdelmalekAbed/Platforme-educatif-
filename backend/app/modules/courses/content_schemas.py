"""Schemas for chapters, resources, quizzes (flat: chapter → items)."""
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Literal, Union
from uuid import UUID
from datetime import datetime


# ---------- Chapters ----------

class ChapterCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None
    position: int = 0


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    position: Optional[int] = None


class ChapterResponse(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    description: Optional[str] = None
    position: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Chapter Resources ----------

class ChapterResourceCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    kind: str = Field(default="pdf")  # video, pdf, exercise, correction, fiche
    url: str = Field(min_length=1, max_length=1000)
    duration_seconds: Optional[int] = None
    position: int = 0


class ChapterResourceUpdate(BaseModel):
    title: Optional[str] = None
    kind: Optional[str] = None
    url: Optional[str] = None
    duration_seconds: Optional[int] = None
    position: Optional[int] = None


class ChapterResourceResponse(BaseModel):
    id: UUID
    chapter_id: UUID
    title: str
    kind: str
    url: str
    duration_seconds: Optional[int] = None
    position: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Quiz ----------

class QuizChoice(BaseModel):
    id: str
    text: str


class QuizQuestionCreate(BaseModel):
    text: str = Field(min_length=1)
    choices: List[QuizChoice]
    correct_choice_id: str
    explanation: Optional[str] = None
    points: float = 1.0
    position: int = 0


class QuizQuestionResponse(BaseModel):
    id: UUID
    quiz_id: UUID
    text: str
    choices: List[Any]
    correct_choice_id: Optional[str] = None
    explanation: Optional[str] = None
    points: float
    position: int

    model_config = {"from_attributes": True}


class QuizQuestionStudentResponse(BaseModel):
    """Same as QuizQuestionResponse but without correct_choice_id."""
    id: UUID
    text: str
    choices: List[Any]
    points: float
    position: int

    model_config = {"from_attributes": True}


class QuizCreate(BaseModel):
    title: str = Field(default="Quiz")
    instructions: Optional[str] = "Lis bien les questions avant de répondre"
    pass_score: float = 50.0
    position: int = 0


class QuizUpdate(BaseModel):
    title: Optional[str] = None
    instructions: Optional[str] = None
    pass_score: Optional[float] = None
    position: Optional[int] = None


class QuizResponse(BaseModel):
    id: UUID
    chapter_id: UUID
    title: str
    instructions: Optional[str] = None
    pass_score: float
    position: int
    questions: List[QuizQuestionResponse] = []

    model_config = {"from_attributes": True}


class QuizStudentResponse(BaseModel):
    """Quiz returned to students — no correct answers."""
    id: UUID
    chapter_id: UUID
    title: str
    instructions: Optional[str] = None
    pass_score: float
    position: int
    questions: List[QuizQuestionStudentResponse] = []

    model_config = {"from_attributes": True}


# ---------- Quiz Attempts ----------

class QuizAnswerSubmission(BaseModel):
    question_id: UUID
    choice_id: str


class QuizAttemptSubmit(BaseModel):
    answers: List[QuizAnswerSubmission]


class QuizAttemptResponse(BaseModel):
    id: UUID
    quiz_id: UUID
    student_id: UUID
    score: float
    correct_count: int
    total_count: int
    answers: List[Any]
    completed_at: datetime

    model_config = {"from_attributes": True}


# ---------- Chapter items (flat list mixing resources + quizzes) ----------

class ChapterItemResource(BaseModel):
    item_type: Literal["resource"] = "resource"
    id: UUID
    title: str
    kind: str
    url: str
    duration_seconds: Optional[int] = None
    position: int
    is_completed: bool = False


class ChapterItemQuiz(BaseModel):
    item_type: Literal["quiz"] = "quiz"
    id: UUID
    title: str
    pass_score: float
    position: int
    question_count: int
    is_completed: bool = False


ChapterItem = Union[ChapterItemResource, ChapterItemQuiz]


class ChapterWithItems(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    position: int
    items_count: int
    items: List[ChapterItem] = []


class CourseWithChapters(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    thumbnail_url: Optional[str] = None
    teacher_id: UUID
    teacher_name: Optional[str] = None
    chapters: List[ChapterWithItems] = []
    progress_percent: float = 0.0

    model_config = {"from_attributes": True}
