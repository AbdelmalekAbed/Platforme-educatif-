from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.core.security.media_tokens import sign_media_url


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CourseAdminCreate(BaseModel):
    teacher_id: UUID
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    max_students: Optional[int] = None
    price: Optional[float] = 0


class SubjectResponse(BaseModel):
    id: UUID
    name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    max_students: Optional[int] = None
    price: Optional[float] = 0


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    max_students: Optional[int] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None


class CourseResponse(BaseModel):
    id: UUID
    teacher_id: UUID
    title: str
    description: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    max_students: Optional[int] = None
    price: Optional[float] = None
    is_active: bool
    thumbnail_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("thumbnail_url")
    def _sign_thumbnail(self, value: Optional[str]) -> Optional[str]:
        # /uploads/* thumbnails leave the backend signed; external URLs pass through.
        return sign_media_url(value)


class SessionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int = 60


class SessionResponse(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int
    status: str
    room_id: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EnrollmentCreate(BaseModel):
    student_id: UUID
    course_id: UUID


class EnrollmentResponse(BaseModel):
    id: UUID
    student_id: UUID
    course_id: UUID
    enrolled_at: datetime
    status: str

    model_config = {"from_attributes": True}
