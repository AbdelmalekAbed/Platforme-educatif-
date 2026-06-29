"""Service métier pour le profil élève et les contacts parentaux.

Les permissions champ-par-champ sont gérées par les routes (via `assert_writable`
de `core/permissions/field_acl.py`). Ce service implémente les invariants
métier : max 2 contacts par élève, un seul `is_primary` à la fois, refus de
supprimer le dernier contact d'un mineur, choix du destinataire de facture, etc.

Le flux de vérification email (génération token + envoi) est isolé dans
`verification_service.py` (lot 3) — ce service expose un hook
`mark_contact_unverified` mais ne touche pas au token.
"""
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, func, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.courses.models import Course, Enrollment
from app.modules.users.models import StudentProfile, TeacherProfile, User
from app.modules.users.parent_models import (
    NotifChannel,
    ParentContact,
    ParentNotifPrefs,
)
from app.modules.users.student_schemas import (
    ParentContactCreate,
    ParentContactUpdate,
    NotifPrefsUpdate,
    EnrollmentSummary,
)


MAX_PARENT_CONTACTS_PER_STUDENT = 2


# ----- Lecture profil -----

async def get_profile_by_id(db: AsyncSession, student_id: UUID) -> StudentProfile | None:
    """Charge un StudentProfile avec User + parent_contacts + notif_prefs préchargés.

    Les enrollments sont chargées séparément via `build_enrollment_summaries`
    pour pouvoir résoudre `teacher_name` (qui nécessite un join à User).
    """
    stmt = (
        select(StudentProfile)
        .where(StudentProfile.id == student_id)
        .options(
            selectinload(StudentProfile.user),
            selectinload(StudentProfile.parent_contacts).selectinload(ParentContact.notif_prefs),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_profile_by_user_id(db: AsyncSession, user_id: UUID) -> StudentProfile | None:
    stmt = (
        select(StudentProfile)
        .where(StudentProfile.user_id == user_id)
        .options(
            selectinload(StudentProfile.user),
            selectinload(StudentProfile.parent_contacts).selectinload(ParentContact.notif_prefs),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def build_enrollment_summaries(
    db: AsyncSession, student_id: UUID
) -> list[EnrollmentSummary]:
    """Retourne les inscriptions de l'élève avec titre du cours + nom du prof."""
    stmt = (
        select(
            Enrollment.id,
            Course.id,
            Course.title,
            Enrollment.status,
            Enrollment.enrolled_at,
            User.first_name,
            User.last_name,
        )
        .join(Course, Course.id == Enrollment.course_id)
        .join(TeacherProfile, TeacherProfile.id == Course.teacher_id)
        .join(User, User.id == TeacherProfile.user_id)
        .where(Enrollment.student_id == student_id)
        .order_by(Enrollment.enrolled_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        EnrollmentSummary(
            enrollment_id=row[0],
            course_id=row[1],
            course_title=row[2],
            status=row[3],
            enrolled_at=row[4],
            teacher_name=f"{row[5]} {row[6]}",
        )
        for row in rows
    ]


# ----- Mise à jour profil -----

async def apply_profile_update(
    db: AsyncSession,
    profile: StudentProfile,
    payload: dict,
) -> StudentProfile:
    """Applique un patch déjà validé (les champs interdits ont été filtrés
    en amont par `assert_writable`). Les champs User sont aiguillés vers
    `profile.user`, les champs StudentProfile vers `profile`.
    """
    USER_FIELDS = {"first_name", "last_name", "phone", "avatar_url"}
    for key, value in payload.items():
        if value is None and key not in {"address", "school_name", "city"}:
            # Skip les valeurs explicitement non fournies (partial update propre)
            continue
        if key in USER_FIELDS:
            setattr(profile.user, key, value)
        elif hasattr(profile, key):
            setattr(profile, key, value)
        # Les champs inconnus ont déjà été filtrés par Pydantic au schéma.
    await db.flush()
    return profile


# ----- Contacts parents -----

async def count_parent_contacts(db: AsyncSession, student_id: UUID) -> int:
    stmt = select(func.count()).select_from(ParentContact).where(
        ParentContact.student_id == student_id
    )
    return (await db.execute(stmt)).scalar_one()


async def list_parent_contacts(
    db: AsyncSession, student_id: UUID
) -> list[ParentContact]:
    stmt = (
        select(ParentContact)
        .where(ParentContact.student_id == student_id)
        .options(selectinload(ParentContact.notif_prefs))
        .order_by(ParentContact.is_primary.desc(), ParentContact.created_at)
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_parent_contact(
    db: AsyncSession, contact_id: UUID
) -> ParentContact | None:
    stmt = (
        select(ParentContact)
        .where(ParentContact.id == contact_id)
        .options(selectinload(ParentContact.notif_prefs))
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def _reset_primary_flag(
    db: AsyncSession, student_id: UUID, except_contact_id: UUID | None = None
) -> None:
    """Force `is_primary=False` sur tous les contacts du student, sauf un.

    Utilisé avant de marquer un contact comme primary, pour respecter la
    contrainte partielle unique `uq_parent_contacts_primary_per_student`.
    """
    stmt = select(ParentContact).where(
        ParentContact.student_id == student_id,
        ParentContact.is_primary.is_(True),
    )
    if except_contact_id is not None:
        stmt = stmt.where(ParentContact.id != except_contact_id)
    others = (await db.execute(stmt)).scalars().all()
    for other in others:
        other.is_primary = False
    if others:
        await db.flush()


async def add_parent_contact(
    db: AsyncSession,
    student_id: UUID,
    data: ParentContactCreate,
) -> ParentContact:
    """Crée un ParentContact (avec ParentNotifPrefs par défaut).

    Invariants :
    - Max 2 contacts par élève → HTTP 400 sinon.
    - Un seul `is_primary=True` à la fois → reset les autres dans la même tx.
    - `is_verified=False` à la création — le token de vérif est généré par
      `verification_service` (lot 3) une fois ce contact persisté.
    """
    current = await count_parent_contacts(db, student_id)
    if current >= MAX_PARENT_CONTACTS_PER_STUDENT:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "max_parent_contacts_reached",
                "message": (
                    f"Un élève peut avoir au maximum "
                    f"{MAX_PARENT_CONTACTS_PER_STUDENT} contacts parentaux."
                ),
            },
        )

    if data.is_primary:
        await _reset_primary_flag(db, student_id)

    contact = ParentContact(
        student_id=student_id,
        full_name=data.full_name,
        relation=data.relation,
        phone=data.phone,
        email=data.email,
        profession=data.profession,
        is_primary=data.is_primary,
        is_verified=False,
    )
    contact.notif_prefs = ParentNotifPrefs(channel=NotifChannel.EMAIL)
    db.add(contact)
    await db.flush()
    return contact


async def update_parent_contact(
    db: AsyncSession,
    contact: ParentContact,
    data: ParentContactUpdate,
) -> ParentContact:
    """Patch partiel d'un ParentContact.

    Effets de bord :
    - Si `email` change → `is_verified` repasse à False (le lot 3 réémettra
      un token de vérification automatiquement).
    - Si `is_primary` passe à True → reset les autres contacts du même élève.
    """
    payload = data.model_dump(exclude_unset=True)

    if "email" in payload and payload["email"] != contact.email:
        contact.is_verified = False
        contact.verification_token_hash = None
        contact.verification_token_expires_at = None

    if payload.get("is_primary") is True:
        await _reset_primary_flag(db, contact.student_id, except_contact_id=contact.id)

    for key, value in payload.items():
        setattr(contact, key, value)
    await db.flush()
    return contact


async def delete_parent_contact(
    db: AsyncSession,
    contact: ParentContact,
    student: StudentProfile,
) -> None:
    """Supprime un contact parental.

    Refus si l'élève est mineur et que c'est le DERNIER contact (sinon on
    perdrait le destinataire des factures et des notifs de mineur).
    """
    if student.is_minor:
        remaining = await count_parent_contacts(db, student.id)
        if remaining <= 1:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "minor_must_have_parent_contact",
                    "message": (
                        "Impossible de supprimer le dernier contact parental "
                        "d'un élève mineur."
                    ),
                },
            )
    await db.delete(contact)
    await db.flush()


async def update_notif_prefs(
    db: AsyncSession,
    contact: ParentContact,
    data: NotifPrefsUpdate,
) -> ParentNotifPrefs:
    """Crée ou met à jour les `ParentNotifPrefs` d'un contact."""
    if contact.notif_prefs is None:
        contact.notif_prefs = ParentNotifPrefs()
        db.add(contact.notif_prefs)
    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        setattr(contact.notif_prefs, key, value)
    await db.flush()
    return contact.notif_prefs


# ----- Helpers pour autres modules -----

async def get_invoice_recipients(
    db: AsyncSession, student: StudentProfile
) -> list[str]:
    """Adresses email à utiliser pour envoyer une facture.

    - Élève majeur : son email uniquement.
    - Élève mineur : contact parental primaire vérifié si présent + email
      élève en fallback. Si aucun parent vérifié, retourne l'email élève seul
      (la facture partira quand même, c'est l'admin qui devra ajuster).
    """
    recipients: list[str] = []
    if student.is_minor:
        primary = next(
            (
                c
                for c in await list_parent_contacts(db, student.id)
                if c.is_primary and c.is_verified
            ),
            None,
        )
        if primary is not None:
            recipients.append(primary.email)
    if student.user and student.user.email:
        recipients.append(student.user.email)
    return recipients


async def can_deactivate_student(
    db: AsyncSession, student: StudentProfile
) -> tuple[bool, ParentContact | None]:
    """Renvoie (autorisé, contact_à_notifier).

    Règle : un élève mineur ne peut pas être désactivé sans qu'il y ait un
    parent vérifié à notifier. Si majeur, désactivation libre.
    """
    if not student.is_minor:
        return True, None
    contacts = await list_parent_contacts(db, student.id)
    primary_verified = next((c for c in contacts if c.is_primary and c.is_verified), None)
    if primary_verified is None:
        return False, None
    return True, primary_verified


async def student_exists(db: AsyncSession, student_id: UUID) -> bool:
    stmt = select(exists().where(StudentProfile.id == student_id))
    return (await db.execute(stmt)).scalar_one()
