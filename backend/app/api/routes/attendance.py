from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.core.permissions import Permission
from app.api.dependencies import get_current_user, require_permission
from app.modules.users.models import User
from app.modules.attendance.schemas import AttendanceResponse, AttendanceUpdate
from app.modules.attendance import service

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("/session/{session_id}", response_model=list[AttendanceResponse])
async def get_session_attendance(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ATTENDANCE_VIEW)),
):
    return await service.get_session_attendance(db, session_id)


@router.get("/student/{student_id}", response_model=list[AttendanceResponse])
async def get_student_attendance(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ATTENDANCE_VIEW)),
):
    return await service.get_student_attendance(db, student_id)


@router.put("/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance(
    attendance_id: UUID,
    data: AttendanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ATTENDANCE_MANAGE)),
):
    attendance = await service.update_attendance_status(db, attendance_id, data.status)
    return attendance
