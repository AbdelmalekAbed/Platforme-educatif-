from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.homework.models import Homework, HomeworkSubmission
from app.modules.homework.schemas import HomeworkCreate, SubmissionCreate, GradeSubmission


async def create_homework(db: AsyncSession, data: HomeworkCreate) -> Homework:
    hw = Homework(
        course_id=data.course_id,
        title=data.title,
        description=data.description,
        due_date=data.due_date,
        max_grade=data.max_grade,
        is_published=data.is_published,
    )
    db.add(hw)
    await db.flush()
    return hw


async def get_homework_by_course(db: AsyncSession, course_id):
    result = await db.execute(
        select(Homework).where(Homework.course_id == course_id).order_by(Homework.created_at.desc())
    )
    return result.scalars().all()


async def get_homework_by_id(db: AsyncSession, homework_id) -> Homework | None:
    result = await db.execute(select(Homework).where(Homework.id == homework_id))
    return result.scalar_one_or_none()


async def submit_homework(db: AsyncSession, student_id, data: SubmissionCreate) -> HomeworkSubmission:
    submission = HomeworkSubmission(
        homework_id=data.homework_id,
        student_id=student_id,
        content=data.content,
        attachment_url=data.attachment_url,
    )
    db.add(submission)
    await db.flush()
    return submission


async def grade_submission(db: AsyncSession, submission: HomeworkSubmission, data: GradeSubmission) -> HomeworkSubmission:
    submission.grade = data.grade
    submission.feedback = data.feedback
    submission.status = "graded"
    submission.graded_at = datetime.now(timezone.utc)
    await db.flush()
    return submission


async def get_submissions_by_homework(db: AsyncSession, homework_id):
    result = await db.execute(
        select(HomeworkSubmission).where(HomeworkSubmission.homework_id == homework_id)
    )
    return result.scalars().all()


async def get_submission_by_id(db: AsyncSession, submission_id) -> HomeworkSubmission | None:
    result = await db.execute(
        select(HomeworkSubmission).where(HomeworkSubmission.id == submission_id)
    )
    return result.scalar_one_or_none()
