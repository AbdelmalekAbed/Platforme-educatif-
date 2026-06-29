import uuid
from datetime import date, datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SAEnum, Text, ForeignKey, Date, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.permissions import Role


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(SAEnum(Role), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    teacher_profile = relationship("TeacherProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    vendor_profile = relationship("VendorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    school_level = Column(String(50), nullable=True)
    school_name = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    preferred_language = Column(String(10), nullable=True, server_default="fr")
    gender = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="student_profile")
    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    homework_submissions = relationship("HomeworkSubmission", back_populates="student", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="student", cascade="all, delete-orphan")
    parent_contacts = relationship(
        "ParentContact",
        back_populates="student",
        cascade="all, delete-orphan",
        order_by="desc(ParentContact.is_primary)",
    )

    @hybrid_property
    def is_minor(self) -> bool:
        if self.date_of_birth is None:
            return True  # par défaut prudent : pas de date connue → traiter comme mineur
        today = date.today()
        years = today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
        return years < 18

    @is_minor.expression
    def is_minor(cls):
        # Côté SQL : age(date_of_birth) < interval '18 years'
        # date_of_birth NULL → is_minor TRUE (cohérent avec le getter Python)
        return (cls.date_of_birth.is_(None)) | (
            func.age(cls.date_of_birth) < text("interval '18 years'")
        )


class TeacherProfile(Base):
    __tablename__ = "teacher_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    bio = Column(Text, nullable=True)
    specialization = Column(String(200), nullable=True)
    qualification = Column(String(200), nullable=True)
    hourly_rate = Column(String(20), nullable=True)

    user = relationship("User", back_populates="teacher_profile")
    courses = relationship("Course", back_populates="teacher", cascade="all, delete-orphan")


class VendorProfile(Base):
    __tablename__ = "vendor_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    company_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    website = Column(String(500), nullable=True)

    user = relationship("User", back_populates="vendor_profile")
