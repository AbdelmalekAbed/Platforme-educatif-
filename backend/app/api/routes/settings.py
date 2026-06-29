"""Platform settings endpoints.

- GET  /admin/settings              → full config (admin only)
- PUT  /admin/settings/{section}    → replace one section (admin only, validated)
- GET  /public/settings             → small subset exposed without auth
"""
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import Role
from app.api.dependencies import require_role
from app.modules.users.models import User
from app.modules.settings import service as settings_service
from app.modules.settings.schemas import (
    AllSettingsResponse,
    PublicSettingsResponse,
    SECTION_SCHEMAS,
)


admin_router = APIRouter(prefix="/admin/settings", tags=["Admin Settings"])
public_router = APIRouter(prefix="/public", tags=["Public"])


@admin_router.get("", response_model=AllSettingsResponse)
async def get_all_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN)),
):
    return await settings_service.get_all(db)


@admin_router.put("/{section}")
async def update_settings_section(
    section: str,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN)),
):
    schema = SECTION_SCHEMAS.get(section)
    if schema is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section inconnue: {section}",
        )
    try:
        validated = schema.model_validate(payload)
    except Exception as exc:  # Pydantic ValidationError formatted message
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    saved = await settings_service.update_section(db, section, validated)
    return saved.model_dump(mode="json")


@public_router.get("/settings", response_model=PublicSettingsResponse)
async def get_public_settings(db: AsyncSession = Depends(get_db)):
    """Exposes the small subset needed by login pages and marketing surfaces."""
    platform = await settings_service.get_section(db, "platform")
    signups = await settings_service.get_section(db, "signups")
    return PublicSettingsResponse(
        name=platform.name,
        description=platform.description,
        support_email=platform.support_email,
        default_language=platform.default_language,
        public_signup_open=signups.public_signup_open,
    )
