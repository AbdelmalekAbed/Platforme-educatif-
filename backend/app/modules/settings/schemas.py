"""Per-section Pydantic schemas. Each schema validates one PUT payload and
matches the section's row value in `platform_settings`. Defaults here are the
seed values returned when a section has never been written."""
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field


class PlatformSection(BaseModel):
    name: str = Field(default="EdTech Platform", min_length=1, max_length=120)
    description: str = Field(default="Plateforme éducative complète", max_length=300)
    support_email: Optional[EmailStr] = Field(default="support@edtech.com")
    default_language: Literal["fr", "en", "ar"] = "fr"
    timezone: str = Field(default="Europe/Paris", max_length=64)


class SignupsSection(BaseModel):
    public_signup_open: bool = True
    require_email_verification: bool = True
    default_role: Literal["student", "teacher"] = "student"
    auto_approve_teachers: bool = False
    require_invite_for_teachers: bool = True


class SecuritySection(BaseModel):
    session_timeout_minutes: int = Field(default=60, ge=5, le=1440)
    password_min_length: int = Field(default=10, ge=6, le=64)
    require_mfa_for_admins: bool = True
    max_login_attempts: int = Field(default=5, ge=1, le=20)


class NotificationsSection(BaseModel):
    email_notifications_global: bool = True
    notify_on_new_signup: bool = True
    notify_on_payment: bool = True
    notify_on_assignment_due: bool = False
    weekly_digest: bool = True


class CoursesSection(BaseModel):
    default_pass_score: float = Field(default=50.0, ge=0, le=100)
    video_max_size_mb: int = Field(default=500, ge=1, le=2000)
    auto_archive_after_days: int = Field(default=365, ge=30, le=3650)
    allow_student_course_rating: bool = True


class AppearanceSection(BaseModel):
    accent_color: str = Field(default="#7c3aed", pattern=r"^#[0-9a-fA-F]{6}$")
    default_theme: Literal["light", "dark", "system"] = "system"


SECTION_SCHEMAS: dict[str, type[BaseModel]] = {
    "platform": PlatformSection,
    "signups": SignupsSection,
    "security": SecuritySection,
    "notifications": NotificationsSection,
    "courses": CoursesSection,
    "appearance": AppearanceSection,
}


class AllSettingsResponse(BaseModel):
    platform: PlatformSection
    signups: SignupsSection
    security: SecuritySection
    notifications: NotificationsSection
    courses: CoursesSection
    appearance: AppearanceSection


class PublicSettingsResponse(BaseModel):
    """Subset safe to expose unauthenticated (used by login page, marketing, etc.)."""
    name: str
    description: str
    support_email: Optional[EmailStr]
    default_language: str
    public_signup_open: bool
