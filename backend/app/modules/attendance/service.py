from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.attendance.models import Attendance


async def mark_present(db: AsyncSession, session_id, student_id) -> Attendance:
    # Check if already exists
    result = await db.execute(
        select(Attendance).where(
            Attendance.session_id == session_id,
            Attendance.student_id == student_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.status = "present"
        existing.joined_at = datetime.now(timezone.utc)
        await db.flush()
        return existing

    attendance = Attendance(
        session_id=session_id,
        student_id=student_id,
        status="present",
        joined_at=datetime.now(timezone.utc),
        auto_marked=True,
    )
    db.add(attendance)
    await db.flush()
    return attendance


async def mark_left(db: AsyncSession, session_id, student_id):
    result = await db.execute(
        select(Attendance).where(
            Attendance.session_id == session_id,
            Attendance.student_id == student_id,
        )
    )
    attendance = result.scalar_one_or_none()
    if attendance:
        attendance.left_at = datetime.now(timezone.utc)
        await db.flush()


async def get_session_attendance(db: AsyncSession, session_id):
    result = await db.execute(
        select(Attendance).where(Attendance.session_id == session_id)
    )
    return result.scalars().all()


async def get_student_attendance(db: AsyncSession, student_id):
    result = await db.execute(
        select(Attendance).where(Attendance.student_id == student_id)
    )
    return result.scalars().all()


async def update_attendance_status(db: AsyncSession, attendance_id, new_status: str):
    result = await db.execute(
        select(Attendance).where(Attendance.id == attendance_id)
    )
    attendance = result.scalar_one_or_none()
    if attendance:
        attendance.status = new_status
        attendance.auto_marked = False
        await db.flush()
    return attendance
