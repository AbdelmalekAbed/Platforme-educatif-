from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class NotificationCreate(BaseModel):
    user_id: UUID
    title: str
    message: Optional[str] = None
    type: str = "info"
    link: Optional[str] = None


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    message: Optional[str] = None
    type: str
    is_read: bool
    link: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
