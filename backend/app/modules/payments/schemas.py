from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class PaymentCreate(BaseModel):
    student_id: UUID
    amount: float
    currency: str = "TND"
    payment_method: Optional[str] = None
    description: Optional[str] = None


class PaymentResponse(BaseModel):
    id: UUID
    student_id: UUID
    amount: float
    currency: str
    status: str
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    paid_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
