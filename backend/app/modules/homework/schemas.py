from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class HomeworkCreate(BaseModel):
    course_id: UUID
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    max_grade: float = 100
    is_published: bool = False


class HomeworkResponse(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    max_grade: float
    attachment_url: Optional[str] = None
    is_published: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SubmissionCreate(BaseModel):
    homework_id: UUID
    content: Optional[str] = None
    attachment_url: Optional[str] = None


class SubmissionResponse(BaseModel):
    id: UUID
    homework_id: UUID
    student_id: UUID
    content: Optional[str] = None
    attachment_url: Optional[str] = None
    grade: Optional[float] = None
    feedback: Optional[str] = None
    submitted_at: datetime
    graded_at: Optional[datetime] = None
    status: str

    model_config = {"from_attributes": True}


class GradeSubmission(BaseModel):
    grade: float
    feedback: Optional[str] = None
