from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.core.permissions import Role, Permission
from app.api.dependencies import get_current_user, require_role, require_permission
from app.modules.users.models import User
from app.modules.payments.schemas import PaymentCreate, PaymentResponse
from app.modules.payments import service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", response_model=PaymentResponse, status_code=201)
async def create_payment(
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PAYMENT_MANAGE)),
):
    return await service.create_payment(db, data)


@router.put("/{payment_id}/complete")
async def complete_payment(
    payment_id: UUID,
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PAYMENT_MANAGE)),
):
    payment = await service.complete_payment(db, payment_id, transaction_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"status": "completed", "payment_id": str(payment.id)}


@router.get("/student/{student_id}", response_model=list[PaymentResponse])
async def get_student_payments(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Students can only see their own payments
    if current_user.role == Role.STUDENT and current_user.student_profile:
        if current_user.student_profile.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
    return await service.get_student_payments(db, student_id)


@router.get("/", response_model=list[PaymentResponse])
async def list_payments(
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PAYMENT_MANAGE)),
):
    return await service.get_all_payments(db, status_filter, skip, limit)
