from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.payments.models import Payment, Invoice
from app.modules.payments.schemas import PaymentCreate
import uuid


async def create_payment(db: AsyncSession, data: PaymentCreate) -> Payment:
    payment = Payment(
        student_id=data.student_id,
        amount=data.amount,
        currency=data.currency,
        payment_method=data.payment_method,
        description=data.description,
    )
    db.add(payment)
    await db.flush()
    return payment


async def complete_payment(db: AsyncSession, payment_id, transaction_id: str) -> Payment | None:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        return None
    payment.status = "completed"
    payment.transaction_id = transaction_id
    payment.paid_at = datetime.now(timezone.utc)

    # Auto-generate invoice
    invoice = Invoice(
        payment_id=payment.id,
        invoice_number=f"INV-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}",
    )
    db.add(invoice)
    await db.flush()
    return payment


async def get_student_payments(db: AsyncSession, student_id):
    result = await db.execute(
        select(Payment).where(Payment.student_id == student_id).order_by(Payment.created_at.desc())
    )
    return result.scalars().all()


async def get_all_payments(db: AsyncSession, status_filter=None, skip=0, limit=50):
    query = select(Payment)
    if status_filter:
        query = query.where(Payment.status == status_filter)
    query = query.offset(skip).limit(limit).order_by(Payment.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()
