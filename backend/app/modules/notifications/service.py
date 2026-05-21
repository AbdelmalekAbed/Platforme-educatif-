from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.modules.notifications.models import Notification
from app.modules.notifications.schemas import NotificationCreate


async def create_notification(db: AsyncSession, data: NotificationCreate) -> Notification:
    notif = Notification(
        user_id=data.user_id,
        title=data.title,
        message=data.message,
        type=data.type,
        link=data.link,
    )
    db.add(notif)
    await db.flush()
    return notif


async def get_user_notifications(db: AsyncSession, user_id, unread_only=False):
    query = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    query = query.order_by(Notification.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


async def mark_as_read(db: AsyncSession, notification_id, user_id):
    await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
        .values(is_read=True)
    )
    await db.flush()


async def mark_all_as_read(db: AsyncSession, user_id):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.flush()
