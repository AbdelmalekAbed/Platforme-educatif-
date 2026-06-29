"""Matrice de permissions champ-par-champ pour le profil élève.

Le `Role` enum (admin/teacher/student/vendor) sert au routing — les permissions
de "qui peut éditer quel champ du profil" sont plus fines : un élève majeur peut
modifier son propre téléphone, un parent peut éditer ses préférences de notif
mais pas le niveau scolaire de l'élève, etc.

Le concept `Actor` ajoute le rôle synthétique `PARENT_OF` qui n'existe pas dans
la table `users` (le parent s'authentifie via un lien tokenisé, pas par compte
User — voir lot 3 du refonte profil).
"""
from enum import Enum


class FieldAction(str, Enum):
    NONE = "none"
    READ = "read"
    WRITE = "write"
    RESET_ONLY = "reset_only"  # cas spécifique du mot de passe : admin peut reset, pas définir


class Actor(str, Enum):
    STUDENT_SELF = "student_self"
    PARENT_OF = "parent_of"
    TEACHER = "teacher"
    ADMIN = "admin"


# Matrice : nom de champ → dict[Actor, FieldAction]
# Les champs absents d'un Actor sont implicitement FieldAction.NONE.
FIELD_ACL: dict[str, dict[Actor, FieldAction]] = {
    "first_name": {
        Actor.STUDENT_SELF: FieldAction.READ,
        Actor.PARENT_OF: FieldAction.READ,
        Actor.TEACHER: FieldAction.READ,
        Actor.ADMIN: FieldAction.WRITE,
    },
    "last_name": {
        Actor.STUDENT_SELF: FieldAction.READ,
        Actor.PARENT_OF: FieldAction.READ,
        Actor.TEACHER: FieldAction.READ,
        Actor.ADMIN: FieldAction.WRITE,
    },
    "email": {
        Actor.STUDENT_SELF: FieldAction.WRITE,
        Actor.ADMIN: FieldAction.WRITE,
    },
    "phone": {
        Actor.STUDENT_SELF: FieldAction.WRITE,
        Actor.ADMIN: FieldAction.WRITE,
    },
    "avatar_url": {
        Actor.STUDENT_SELF: FieldAction.WRITE,
        Actor.ADMIN: FieldAction.WRITE,
    },
    "date_of_birth": {
        Actor.STUDENT_SELF: FieldAction.READ,
        Actor.PARENT_OF: FieldAction.READ,
        Actor.ADMIN: FieldAction.WRITE,
    },
    "school_level": {
        Actor.STUDENT_SELF: FieldAction.READ,
        Actor.PARENT_OF: FieldAction.READ,
        Actor.ADMIN: FieldAction.WRITE,
    },
    "school_name": {
        Actor.STUDENT_SELF: FieldAction.READ,
        Actor.PARENT_OF: FieldAction.READ,
        Actor.ADMIN: FieldAction.WRITE,
    },
    "city": {
        Actor.STUDENT_SELF: FieldAction.READ,
        Actor.PARENT_OF: FieldAction.READ,
        Actor.ADMIN: FieldAction.WRITE,
    },
    "address": {
        Actor.STUDENT_SELF: FieldAction.READ,
        Actor.PARENT_OF: FieldAction.READ,
        Actor.ADMIN: FieldAction.WRITE,
    },
    "preferred_language": {
        Actor.STUDENT_SELF: FieldAction.WRITE,
        Actor.ADMIN: FieldAction.WRITE,
    },
    "gender": {
        Actor.STUDENT_SELF: FieldAction.READ,
        Actor.ADMIN: FieldAction.WRITE,
    },
    "parent_contacts": {
        Actor.STUDENT_SELF: FieldAction.READ,
        Actor.PARENT_OF: FieldAction.WRITE,  # partiel — voir student_service
        Actor.ADMIN: FieldAction.WRITE,
    },
    "notif_prefs": {
        Actor.PARENT_OF: FieldAction.WRITE,
        Actor.ADMIN: FieldAction.WRITE,
    },
    "enrollments": {
        Actor.STUDENT_SELF: FieldAction.READ,
        Actor.PARENT_OF: FieldAction.READ,
        Actor.TEACHER: FieldAction.READ,
        Actor.ADMIN: FieldAction.WRITE,
    },
    "password": {
        Actor.STUDENT_SELF: FieldAction.WRITE,
        Actor.ADMIN: FieldAction.RESET_ONLY,
    },
}


def get_action(actor: Actor, field: str) -> FieldAction:
    """Action autorisée pour `actor` sur `field`. Défaut : NONE."""
    return FIELD_ACL.get(field, {}).get(actor, FieldAction.NONE)


def is_readable(actor: Actor, field: str) -> bool:
    return get_action(actor, field) in (FieldAction.READ, FieldAction.WRITE, FieldAction.RESET_ONLY)


def is_writable(actor: Actor, field: str) -> bool:
    return get_action(actor, field) == FieldAction.WRITE


def filter_readable(actor: Actor, payload: dict) -> dict:
    """Retire d'un dict les clés que `actor` ne peut pas lire.

    Sémantique : la matrice est une **scope-list**, pas une whitelist complète.
    Les champs absents de `FIELD_ACL` (`id`, `user_id`, `is_minor`, métadonnées
    structurelles…) sont considérés comme toujours lisibles. Seuls les champs
    EXPLICITEMENT listés dans la matrice peuvent être retirés.
    """
    return {
        k: v
        for k, v in payload.items()
        if k not in FIELD_ACL or is_readable(actor, k)
    }


def assert_writable(actor: Actor, fields: list[str]) -> None:
    """Lève HTTPException 403 si `actor` tente d'écrire un champ interdit.

    Import local pour éviter la dépendance circulaire avec FastAPI au niveau du
    package permissions (utilisé en module pur ailleurs).
    """
    forbidden = [f for f in fields if not is_writable(actor, f)]
    if forbidden:
        from fastapi import HTTPException  # noqa: PLC0415
        raise HTTPException(
            status_code=403,
            detail={
                "code": "forbidden_fields",
                "message": "Certains champs sont en lecture seule pour ce rôle.",
                "fields": forbidden,
            },
        )


def acl_summary_for(actor: Actor) -> dict[str, str]:
    """Retourne {champ: action} pour exposer la matrice côté front.

    Utilisé par `GET /students/me/field-permissions` pour éviter le drift
    frontend/backend.
    """
    return {field: get_action(actor, field).value for field in FIELD_ACL.keys()}
