"""Routes REST pour le profil élève et les contacts parentaux.

Composé de 2 routers :
- `students_router` (`/students/...`) : profil + ACL + contacts via student_id
- `parent_contacts_router` (`/parent-contacts/...`) : opérations sur un contact
  par son propre id (édition, suppression, prefs notif).
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user, require_role
from app.api.dependencies.student import (
    get_my_student_profile,
    resolve_student_actor,
)
from app.core.database import get_db
from app.core.permissions import (
    Actor,
    Role,
    acl_summary_for,
    assert_writable,
    filter_readable,
)
from app.modules.users import student_service
from app.modules.users.models import StudentProfile, User
from app.modules.users.parent_models import ParentContact
from app.modules.users.student_schemas import (
    FieldACLSummary,
    NotifPrefsRead,
    NotifPrefsUpdate,
    ParentContactCreate,
    ParentContactRead,
    ParentContactUpdate,
    StudentProfileAdminUpdate,
    StudentProfileReadFull,
    StudentProfileSelfUpdate,
)


students_router = APIRouter(prefix="/students", tags=["Students"])
parent_contacts_router = APIRouter(prefix="/parent-contacts", tags=["Parent Contacts"])


# ----- Helpers internes -----

async def _build_full_read(
    db: AsyncSession, profile: StudentProfile, actor: Actor
) -> dict:
    """Construit le payload `StudentProfileReadFull` + filtre selon l'ACL."""
    enrollments = await student_service.build_enrollment_summaries(db, profile.id)
    payload = {
        "id": profile.id,
        "user_id": profile.user_id,
        "first_name": profile.user.first_name,
        "last_name": profile.user.last_name,
        "email": profile.user.email,
        "phone": profile.user.phone,
        "avatar_url": profile.user.avatar_url,
        "is_minor": profile.is_minor,
        "date_of_birth": profile.date_of_birth,
        "school_level": profile.school_level,
        "school_name": profile.school_name,
        "address": profile.address,
        "city": profile.city,
        "preferred_language": profile.preferred_language,
        "gender": profile.gender,
        "parent_contacts": profile.parent_contacts,
        "enrollments": enrollments,
    }
    # Sérialisation forte via Pydantic puis filtrage selon la matrice.
    # `filter_readable` ne retire QUE les champs explicitement listés dans
    # FIELD_ACL — `id`, `user_id`, `is_minor`, `enrollments` passent tels quels.
    dto = StudentProfileReadFull.model_validate(payload).model_dump(mode="json")
    return filter_readable(actor, dto)


def _ensure_admin_or_self(profile: StudentProfile, current_user: User) -> Actor:
    """Variante allégée du résolveur d'acteur quand le profil est déjà chargé."""
    if current_user.role == Role.ADMIN:
        return Actor.ADMIN
    if current_user.role == Role.STUDENT and profile.user_id == current_user.id:
        return Actor.STUDENT_SELF
    raise HTTPException(status_code=403, detail="Accès refusé.")


# ----- /students/me -----

@students_router.get("/me")
async def read_my_profile(
    profile: StudentProfile = Depends(get_my_student_profile),
    db: AsyncSession = Depends(get_db),
):
    return await _build_full_read(db, profile, Actor.STUDENT_SELF)


@students_router.get("/me/field-permissions", response_model=FieldACLSummary)
async def read_my_field_permissions(
    profile: StudentProfile = Depends(get_my_student_profile),
):
    return FieldACLSummary(
        actor=Actor.STUDENT_SELF.value,
        fields=acl_summary_for(Actor.STUDENT_SELF),
    )


@students_router.patch("/me")
async def update_my_profile(
    data: StudentProfileSelfUpdate,
    profile: StudentProfile = Depends(get_my_student_profile),
    db: AsyncSession = Depends(get_db),
):
    payload = data.model_dump(exclude_unset=True)
    assert_writable(Actor.STUDENT_SELF, list(payload.keys()))
    updated = await student_service.apply_profile_update(db, profile, payload)
    return await _build_full_read(db, updated, Actor.STUDENT_SELF)


# ----- /students/{id} (admin / teacher / student self) -----

@students_router.get("/{student_id}")
async def read_student_profile(
    actor_and_profile: tuple[Actor, StudentProfile] = Depends(resolve_student_actor),
    db: AsyncSession = Depends(get_db),
):
    actor, profile = actor_and_profile
    return await _build_full_read(db, profile, actor)


@students_router.get("/{student_id}/field-permissions", response_model=FieldACLSummary)
async def read_student_field_permissions(
    actor_and_profile: tuple[Actor, StudentProfile] = Depends(resolve_student_actor),
):
    actor, _ = actor_and_profile
    return FieldACLSummary(actor=actor.value, fields=acl_summary_for(actor))


@students_router.patch("/{student_id}")
async def admin_update_student_profile(
    data: StudentProfileAdminUpdate,
    actor_and_profile: tuple[Actor, StudentProfile] = Depends(resolve_student_actor),
    db: AsyncSession = Depends(get_db),
):
    actor, profile = actor_and_profile
    payload = data.model_dump(exclude_unset=True)
    assert_writable(actor, list(payload.keys()))
    updated = await student_service.apply_profile_update(db, profile, payload)
    return await _build_full_read(db, updated, actor)


# ----- Contacts parents (côté /students/{id}/parent-contacts) -----

@students_router.get(
    "/{student_id}/parent-contacts", response_model=list[ParentContactRead]
)
async def list_student_parent_contacts(
    actor_and_profile: tuple[Actor, StudentProfile] = Depends(resolve_student_actor),
    db: AsyncSession = Depends(get_db),
):
    _, profile = actor_and_profile
    return await student_service.list_parent_contacts(db, profile.id)


@students_router.post(
    "/{student_id}/parent-contacts",
    response_model=ParentContactRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_student_parent_contact(
    data: ParentContactCreate,
    actor_and_profile: tuple[Actor, StudentProfile] = Depends(resolve_student_actor),
    db: AsyncSession = Depends(get_db),
):
    actor, profile = actor_and_profile
    assert_writable(actor, ["parent_contacts"])
    contact = await student_service.add_parent_contact(db, profile.id, data)
    # TODO lot 3 : déclencher l'envoi de l'email de vérification.
    return contact


# ----- Routes sur un contact (par contact_id) -----

async def _load_contact_or_404(db: AsyncSession, contact_id: UUID) -> ParentContact:
    contact = await student_service.get_parent_contact(db, contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact parental introuvable.")
    return contact


@parent_contacts_router.patch("/{contact_id}", response_model=ParentContactRead)
async def update_parent_contact(
    contact_id: UUID,
    data: ParentContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = await _load_contact_or_404(db, contact_id)
    profile = await student_service.get_profile_by_id(db, contact.student_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Élève introuvable.")
    actor = _ensure_admin_or_self(profile, current_user)
    assert_writable(actor, ["parent_contacts"])
    return await student_service.update_parent_contact(db, contact, data)


@parent_contacts_router.delete(
    "/{contact_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_parent_contact(
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    contact = await _load_contact_or_404(db, contact_id)
    profile = await student_service.get_profile_by_id(db, contact.student_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Élève introuvable.")
    await student_service.delete_parent_contact(db, contact, profile)


@parent_contacts_router.put("/{contact_id}/notif-prefs", response_model=NotifPrefsRead)
async def update_parent_notif_prefs(
    contact_id: UUID,
    data: NotifPrefsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    contact = await _load_contact_or_404(db, contact_id)
    return await student_service.update_notif_prefs(db, contact, data)


@parent_contacts_router.post(
    "/{contact_id}/resend-verification", status_code=status.HTTP_501_NOT_IMPLEMENTED
)
async def resend_parent_verification(
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stub — implémenté au lot 3 (génération token + envoi email)."""
    await _load_contact_or_404(db, contact_id)
    raise HTTPException(
        status_code=501,
        detail="Flux de vérification parent : implémenté au lot 3.",
    )
