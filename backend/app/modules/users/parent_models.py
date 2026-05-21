import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ParentRelation(str, enum.Enum):
    FATHER = "pere"
    MOTHER = "mere"
    LEGAL_GUARDIAN = "tuteur_legal"
    OTHER = "autre"


class NotifChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    BOTH = "both"


class ParentContact(Base):
    __tablename__ = "parent_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_name = Column(String(200), nullable=False)
    relation = Column(SAEnum(ParentRelation, name="parent_relation"), nullable=False)
    phone = Column(String(30), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    profession = Column(String(200), nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    is_primary = Column(Boolean, nullable=False, default=False)
    verification_token_hash = Column(String(64), nullable=True, unique=True)
    verification_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    verification_sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    student = relationship("StudentProfile", back_populates="parent_contacts")
    notif_prefs = relationship(
        "ParentNotifPrefs",
        back_populates="parent",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ParentNotifPrefs(Base):
    __tablename__ = "parent_notif_prefs"

    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("parent_contacts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    invoices = Column(Boolean, nullable=False, default=True)
    absences = Column(Boolean, nullable=False, default=True)
    grades = Column(Boolean, nullable=False, default=True)
    reports = Column(Boolean, nullable=False, default=True)
    reminders = Column(Boolean, nullable=False, default=True)
    channel = Column(
        SAEnum(NotifChannel, name="notif_channel"),
        nullable=False,
        default=NotifChannel.EMAIL,
    )

    parent = relationship("ParentContact", back_populates="notif_prefs")
