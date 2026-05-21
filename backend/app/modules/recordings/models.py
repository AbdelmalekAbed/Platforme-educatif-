import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Recording(Base):
    __tablename__ = "recordings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("course_sessions.id", ondelete="CASCADE"), unique=True, nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size_mb = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    status = Column(String(20), default="processing")  # processing, ready, failed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session = relationship("CourseSession", back_populates="recording")
