from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class AttendanceResponse(BaseModel):
    id: UUID
    session_id: UUID
    student_id: UUID
    status: str
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None
    auto_marked: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AttendanceUpdate(BaseModel):
    status: str  # present, absent, late, excused
