from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.modules.users.models import User
from app.modules.notifications.schemas import NotificationResponse
from app.modules.notifications import service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await service.get_user_notifications(db, current_user.id, unread_only)


@router.put("/{notification_id}/read")
async def mark_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await service.mark_as_read(db, notification_id, current_user.id)
    return {"status": "ok"}


@router.put("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await service.mark_all_as_read(db, current_user.id)
    return {"status": "ok"}
