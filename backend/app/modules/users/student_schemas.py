"""Schemas Pydantic pour le profil élève (lecture, mises à jour, contacts parents).

Les schemas legacy de `auth/schemas.py` (`StudentProfileResponse` / `Update`)
sont conservés pour compat mais ne devraient plus être utilisés — les nouvelles
routes `/students/...` utilisent les schemas définis ici.
"""
from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.users.parent_models import NotifChannel, ParentRelation


# ----- Énumérations applicatives (non DB) -----

Gender = Literal["male", "female", "other", "prefer_not_to_say"]
PreferredLanguage = Literal["fr", "ar", "en"]


# ----- StudentProfile -----

class StudentProfileBase(BaseModel):
    """Champs communs (modifiables sous condition selon l'acteur)."""
    date_of_birth: Optional[date] = None
    school_level: Optional[str] = Field(None, max_length=50)
    school_name: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    preferred_language: Optional[PreferredLanguage] = None
    gender: Optional[Gender] = None


class EnrollmentSummary(BaseModel):
    enrollment_id: UUID
    course_id: UUID
    course_title: str
    teacher_name: str
    status: str
    enrolled_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentProfileReadFull(StudentProfileBase):
    """Réponse complète pour GET /students/{id} et /students/me.

    Les champs User (first_name, last_name, email, phone, avatar_url) sont
    aplatis pour simplifier la consommation côté frontend.
    """
    id: UUID
    user_id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_minor: bool
    parent_contacts: list["ParentContactRead"] = []
    enrollments: list[EnrollmentSummary] = []

    model_config = ConfigDict(from_attributes=True)


class StudentProfileAdminUpdate(BaseModel):
    """PATCH /students/{id} — admin peut tout modifier sauf email/password
    (endpoints dédiés côté `/account/...`).
    """
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    school_level: Optional[str] = Field(None, max_length=50)
    school_name: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    preferred_language: Optional[PreferredLanguage] = None
    gender: Optional[Gender] = None
    avatar_url: Optional[str] = Field(None, max_length=500)


class StudentProfileSelfUpdate(BaseModel):
    """PATCH /students/me — l'élève ne peut modifier que ce que la matrice
    permet (avatar, phone, preferred_language). L'email passe par
    `/account/email` (avec confirmation mot de passe).
    """
    avatar_url: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    preferred_language: Optional[PreferredLanguage] = None


# ----- ParentContact -----

class ParentContactBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    relation: ParentRelation
    phone: Optional[str] = Field(None, max_length=30)
    email: EmailStr
    profession: Optional[str] = Field(None, max_length=200)


class ParentContactCreate(ParentContactBase):
    is_primary: bool = False


class ParentContactUpdate(BaseModel):
    """Mise à jour partielle. Si `email` change → re-vérification automatique
    côté service (is_verified passe à False, nouveau token envoyé)."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    relation: Optional[ParentRelation] = None
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    profession: Optional[str] = Field(None, max_length=200)
    is_primary: Optional[bool] = None


class NotifPrefsRead(BaseModel):
    invoices: bool
    absences: bool
    grades: bool
    reports: bool
    reminders: bool
    channel: NotifChannel

    model_config = ConfigDict(from_attributes=True)


class NotifPrefsUpdate(BaseModel):
    invoices: Optional[bool] = None
    absences: Optional[bool] = None
    grades: Optional[bool] = None
    reports: Optional[bool] = None
    reminders: Optional[bool] = None
    channel: Optional[NotifChannel] = None


class ParentContactRead(ParentContactBase):
    id: UUID
    student_id: UUID
    is_verified: bool
    is_primary: bool
    verification_sent_at: Optional[datetime] = None
    notif_prefs: Optional[NotifPrefsRead] = None

    model_config = ConfigDict(from_attributes=True)


# Permet la forward reference dans StudentProfileReadFull
StudentProfileReadFull.model_rebuild()


# ----- ACL summary (exposée par l'API pour éviter drift front/back) -----

class FieldACLSummary(BaseModel):
    """Réponse de GET /students/me/field-permissions.

    `actor` indique l'identité résolue côté serveur (student_self / admin /
    teacher / parent_of). `fields` est un dict {champ: action} pour les
    16 champs gérés par la matrice.
    """
    actor: str
    fields: dict[str, str]
