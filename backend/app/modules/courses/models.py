import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, Float, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teacher_profiles.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    subject = Column(String(100), nullable=True)
    grade_level = Column(String(50), nullable=True)
    max_students = Column(Integer, nullable=True)
    price = Column(Float, nullable=True, default=0)
    is_active = Column(Boolean, default=True)
    thumbnail_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    teacher = relationship("TeacherProfile", back_populates="courses")
    sessions = relationship("CourseSession", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    homework = relationship("Homework", back_populates="course", cascade="all, delete-orphan")
    resources = relationship("CourseResource", back_populates="course", cascade="all, delete-orphan")
    chapters = relationship("Chapter", back_populates="course", cascade="all, delete-orphan", order_by="Chapter.position")


class CourseSession(Base):
    __tablename__ = "course_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=60)
    status = Column(String(20), default="scheduled")  # scheduled, live, completed, cancelled
    room_id = Column(String(100), nullable=True)  # WebRTC room identifier
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    course = relationship("Course", back_populates="sessions")
    attendances = relationship("Attendance", back_populates="session", cascade="all, delete-orphan")
    recording = relationship("Recording", back_populates="session", uselist=False, cascade="all, delete-orphan")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    enrolled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default="active")  # active, completed, dropped

    student = relationship("StudentProfile", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


class CourseResource(Base):
    __tablename__ = "course_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(300), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    course = relationship("Course", back_populates="resources")


class Chapter(Base):
    """Course chapter (e.g. 'Aire, Périmètre et Volume 3ème')."""
    __tablename__ = "chapters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    position = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    course = relationship("Course", back_populates="chapters")
    resources = relationship("ChapterResource", back_populates="chapter", cascade="all, delete-orphan", order_by="ChapterResource.position")
    quizzes = relationship("Quiz", back_populates="chapter", cascade="all, delete-orphan", order_by="Quiz.position")


class ChapterResource(Base):
    """Pedagogical file (video / pdf / exercise / fiche) attached directly to a chapter."""
    __tablename__ = "chapter_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(300), nullable=False)
    # Resource kinds: video, pdf, exercise, correction, fiche
    kind = Column(String(30), nullable=False, default="pdf")
    url = Column(String(1000), nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    position = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    chapter = relationship("Chapter", back_populates="resources")
    progress = relationship("ChapterResourceProgress", back_populates="resource", cascade="all, delete-orphan")


class Quiz(Base):
    """Quiz item attached to a chapter (ordered alongside resources via `position`)."""
    __tablename__ = "quizzes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(300), nullable=False, default="Quiz")
    instructions = Column(Text, nullable=True, default="Lis bien les questions avant de répondre")
    pass_score = Column(Float, default=50.0)  # percentage
    position = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    chapter = relationship("Chapter", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan", order_by="QuizQuestion.position")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    """A question inside a quiz with multiple-choice answers."""
    __tablename__ = "quiz_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    # choices: list of {"id": "a", "text": "..."}
    choices = Column(JSON, nullable=False, default=list)
    correct_choice_id = Column(String(20), nullable=False)
    explanation = Column(Text, nullable=True)
    points = Column(Float, default=1.0)
    position = Column(Integer, default=0)

    quiz = relationship("Quiz", back_populates="questions")


class QuizAttempt(Base):
    """A student's attempt at a quiz with score."""
    __tablename__ = "quiz_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    score = Column(Float, default=0.0)  # percentage
    correct_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    # answers: list of {"question_id": "...", "choice_id": "...", "is_correct": bool}
    answers = Column(JSON, nullable=False, default=list)
    completed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    quiz = relationship("Quiz", back_populates="attempts")


class ChapterResourceProgress(Base):
    """Tracks which chapter resources a student has visited/completed."""
    __tablename__ = "chapter_resource_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("chapter_resources.id", ondelete="CASCADE"), nullable=False)
    is_completed = Column(Boolean, default=False)
    visited_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    resource = relationship("ChapterResource", back_populates="progress")


class StudentCourseKnown(Base):
    """Student-declared 'I already know this whole course'. Forces 100% progress without erasing actual visits."""
    __tablename__ = "student_course_known"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_student_course_known"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    marked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class StudentChapterKnown(Base):
    """Student-declared 'I already know this chapter'. Forces all its items to count as completed."""
    __tablename__ = "student_chapter_known"
    __table_args__ = (
        UniqueConstraint("student_id", "chapter_id", name="uq_student_chapter_known"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    marked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
