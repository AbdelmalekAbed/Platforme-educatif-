import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="TND")
    status = Column(String(20), default="pending")  # pending, completed, failed, refunded
    payment_method = Column(String(50), nullable=True)  # flouci, konnect, stripe, cash
    transaction_id = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    paid_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("StudentProfile", back_populates="payments")
    invoice = relationship("Invoice", back_populates="payment", uselist=False, cascade="all, delete-orphan")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="CASCADE"), unique=True, nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False)
    issued_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    pdf_url = Column(String(500), nullable=True)

    payment = relationship("Payment", back_populates="invoice")
