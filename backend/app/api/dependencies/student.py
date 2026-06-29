"""Dépendances FastAPI spécifiques au profil élève.

Résout l'`Actor` à partir d'un `current_user` et d'un `student_id` :
- ADMIN → quel que soit l'élève visé.
- STUDENT_SELF → si current_user.id == profile.user_id.
- TEACHER → si l'enseignant courant a au moins un cours auquel l'élève est inscrit.

Le cas `PARENT_OF` n'est pas géré ici — il sera ajouté au lot 3 (portail
parent via token), avec une dépendance dédiée `get_current_parent`.
"""
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.core.permissions import Actor, Role
from app.modules.courses.models import Course, Enrollment
from app.modules.users import student_service
from app.modules.users.models import StudentProfile, TeacherProfile, User


async def _teacher_owns_enrollment(
    db: AsyncSession, teacher_user_id: UUID, student_id: UUID
) -> bool:
    stmt = select(
        exists().where(
            Enrollment.student_id == student_id,
            Enrollment.course_id == Course.id,
            Course.teacher_id == TeacherProfile.id,
            TeacherProfile.user_id == teacher_user_id,
        )
    )
    return (await db.execute(stmt)).scalar_one()


async def resolve_student_actor(
    student_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[Actor, StudentProfile]:
    """Résout l'Actor pour un `student_id` donné + charge le profil.

    Lève HTTPException 404 si l'élève n'existe pas, 403 si l'utilisateur
    courant n'a aucun rôle légitime sur ce profil.
    """
    profile = await student_service.get_profile_by_id(db, student_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Élève introuvable")

    if current_user.role == Role.ADMIN:
        return Actor.ADMIN, profile

    if current_user.role == Role.STUDENT and profile.user_id == current_user.id:
        return Actor.STUDENT_SELF, profile

    if current_user.role == Role.TEACHER:
        if await _teacher_owns_enrollment(db, current_user.id, student_id):
            return Actor.TEACHER, profile

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Accès refusé à ce profil élève.",
    )


async def get_my_student_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StudentProfile:
    """Variante self-service : récupère le profil de l'élève courant.

    Réservée à `Role.STUDENT`. Lève 404 si l'utilisateur n'a pas (encore)
    de `StudentProfile` lié (cas edge : compte créé sans profil).
    """
    if current_user.role != Role.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cet endpoint est réservé aux élèves.",
        )
    profile = await student_service.get_profile_by_user_id(db, current_user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profil élève introuvable")
    return profile
