"""Platform-wide configuration storage.

Single table holding one JSON blob per section (platform, signups, security, ...).
Sections that haven't been written yet fall back to the defaults defined in
`defaults.py`, so the table can be empty on a fresh install.
"""
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class PlatformSetting(Base):
    __tablename__ = "platform_settings"

    # Section key: "platform", "signups", "security", "notifications", "courses",
    # "appearance". One row per section, value is the full section payload.
    key = Column(String, primary_key=True)
    value = Column(JSONB, nullable=False, default=dict)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
