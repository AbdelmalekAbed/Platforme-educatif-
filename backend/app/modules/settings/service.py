"""Read/write helpers for platform settings.

Falls back to schema defaults when a section row doesn't exist yet, so the rest
of the codebase can call `get_section(db, "courses")` without first checking
whether the admin has ever opened the settings page.
"""
from typing import Type
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.modules.settings.models import PlatformSetting
from app.modules.settings.schemas import (
    SECTION_SCHEMAS,
    AllSettingsResponse,
)


async def get_section(db: AsyncSession, key: str) -> BaseModel:
    """Return the validated section, falling back to the schema's defaults."""
    schema = SECTION_SCHEMAS.get(key)
    if schema is None:
        raise ValueError(f"Unknown settings section: {key}")
    row = await db.get(PlatformSetting, key)
    if row is None or not isinstance(row.value, dict):
        return schema()
    # Merge stored value over defaults so partially-written rows still validate
    # after a schema upgrade (new field added → falls back to default).
    return schema.model_validate({**schema().model_dump(), **row.value})


async def get_all(db: AsyncSession) -> AllSettingsResponse:
    sections = {key: await get_section(db, key) for key in SECTION_SCHEMAS}
    return AllSettingsResponse(**sections)


async def update_section(
    db: AsyncSession,
    key: str,
    payload: BaseModel,
) -> BaseModel:
    """Replace the section's stored value with `payload`. Returns what was saved."""
    if key not in SECTION_SCHEMAS:
        raise ValueError(f"Unknown settings section: {key}")
    data = payload.model_dump(mode="json")
    row = await db.get(PlatformSetting, key)
    if row is None:
        row = PlatformSetting(key=key, value=data)
        db.add(row)
    else:
        row.value = data
    await db.flush()
    return payload


def get_schema(key: str) -> Type[BaseModel]:
    schema = SECTION_SCHEMAS.get(key)
    if schema is None:
        raise ValueError(f"Unknown settings section: {key}")
    return schema
