from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.core.permissions import Role, Permission
from app.api.dependencies import get_current_user, require_permission
from app.modules.users.models import User
from app.modules.homework.schemas import (
    HomeworkCreate, HomeworkResponse, SubmissionCreate, SubmissionResponse, GradeSubmission,
)
from app.modules.homework import service

router = APIRouter(prefix="/homework", tags=["Homework"])


@router.post("/", response_model=HomeworkResponse, status_code=status.HTTP_201_CREATED)
async def create_homework(
    data: HomeworkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.HOMEWORK_CREATE)),
):
    hw = await service.create_homework(db, data)
    return hw


@router.get("/course/{course_id}", response_model=list[HomeworkResponse])
async def list_homework(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.HOMEWORK_READ)),
):
    return await service.get_homework_by_course(db, course_id)


@router.post("/submit", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_homework(
    data: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.HOMEWORK_SUBMIT)),
):
    if not current_user.student_profile:
        raise HTTPException(status_code=400, detail="Student profile required")
    submission = await service.submit_homework(db, current_user.student_profile.id, data)
    return submission


@router.get("/{homework_id}/submissions", response_model=list[SubmissionResponse])
async def list_submissions(
    homework_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.HOMEWORK_GRADE)),
):
    return await service.get_submissions_by_homework(db, homework_id)


@router.put("/submissions/{submission_id}/grade", response_model=SubmissionResponse)
async def grade_submission(
    submission_id: UUID,
    data: GradeSubmission,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.HOMEWORK_GRADE)),
):
    submission = await service.get_submission_by_id(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return await service.grade_submission(db, submission, data)
