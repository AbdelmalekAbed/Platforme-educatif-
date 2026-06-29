from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from uuid import UUID
from app.core.database import get_db
from app.core.permissions import Role, Permission
from app.api.dependencies import get_current_user, require_role, require_permission
from app.modules.users.models import User
from app.modules.courses.models import (
    Subject, Course, Enrollment, CourseSession,
    Chapter, ChapterResource, ChapterResourceProgress, Quiz, QuizAttempt,
)
from app.modules.homework.models import Homework
from app.modules.courses.schemas import (
    CourseCreate, CourseUpdate, CourseResponse, SessionCreate, SessionResponse,
    EnrollmentCreate, EnrollmentResponse, SubjectResponse,
)
from app.modules.courses import service
from app.modules.notifications import service as notif_service
from app.modules.notifications.schemas import NotificationCreate

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/subjects", response_model=list[SubjectResponse])
async def list_active_subjects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Subject).where(Subject.is_active == True).order_by(Subject.name)
    )
    return result.scalars().all()


@router.get("/teacher-dashboard")
async def teacher_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.TEACHER)),
):
    """Aggregated stats for the teacher dashboard: totals + per-course breakdown."""
    if not current_user.teacher_profile:
        raise HTTPException(status_code=400, detail="Teacher profile not found")
    teacher_id = current_user.teacher_profile.id
    now = datetime.now(timezone.utc)

    # All teacher's courses
    courses_res = await db.execute(
        select(Course).where(Course.teacher_id == teacher_id).order_by(Course.created_at.desc())
    )
    courses = courses_res.scalars().all()
    course_ids = [c.id for c in courses]

    if course_ids:
        students_res = await db.execute(
            select(func.count(func.distinct(Enrollment.student_id)))
            .where(Enrollment.course_id.in_(course_ids))
        )
        total_students = students_res.scalar() or 0

        upcoming_res = await db.execute(
            select(func.count(CourseSession.id))
            .where(CourseSession.course_id.in_(course_ids))
            .where(CourseSession.scheduled_at >= now)
            .where(CourseSession.status != "cancelled")
        )
        upcoming_sessions = upcoming_res.scalar() or 0

        hw_res = await db.execute(
            select(func.count(Homework.id))
            .where(Homework.course_id.in_(course_ids))
            .where(Homework.is_published == True)
            .where(or_(Homework.due_date.is_(None), Homework.due_date >= now))
        )
        active_homework = hw_res.scalar() or 0
    else:
        total_students = 0
        upcoming_sessions = 0
        active_homework = 0

    # Per-course aggregates
    course_cards = []
    for c in courses:
        chapter_count_res = await db.execute(
            select(func.count(Chapter.id)).where(Chapter.course_id == c.id)
        )
        chapter_count = chapter_count_res.scalar() or 0

        student_count_res = await db.execute(
            select(func.count(Enrollment.id)).where(Enrollment.course_id == c.id)
        )
        student_count = student_count_res.scalar() or 0

        total_items_res = await db.execute(
            select(
                func.count(ChapterResource.id),
            ).select_from(Chapter).join(
                ChapterResource, ChapterResource.chapter_id == Chapter.id, isouter=True
            ).where(Chapter.course_id == c.id)
        )
        total_resources = total_items_res.scalar() or 0
        total_quizzes_res = await db.execute(
            select(func.count(Quiz.id)).select_from(Chapter).join(
                Quiz, Quiz.chapter_id == Chapter.id, isouter=True
            ).where(Chapter.course_id == c.id)
        )
        total_quizzes = total_quizzes_res.scalar() or 0
        total_items = total_resources + total_quizzes

        avg_progress = None
        if student_count > 0 and total_items > 0:
            completed_res = await db.execute(
                select(func.count(ChapterResourceProgress.id))
                .select_from(ChapterResourceProgress)
                .join(ChapterResource, ChapterResource.id == ChapterResourceProgress.resource_id)
                .join(Chapter, Chapter.id == ChapterResource.chapter_id)
                .where(Chapter.course_id == c.id)
                .where(ChapterResourceProgress.is_completed.is_(True))
            )
            completed_resources = completed_res.scalar() or 0

            passed_qz_res = await db.execute(
                select(func.count(func.distinct(func.concat(QuizAttempt.student_id, QuizAttempt.quiz_id))))
                .select_from(QuizAttempt)
                .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
                .join(Chapter, Chapter.id == Quiz.chapter_id)
                .where(Chapter.course_id == c.id)
                .where(QuizAttempt.score >= Quiz.pass_score)
            )
            passed_quizzes = passed_qz_res.scalar() or 0

            avg_progress = round(
                ((completed_resources + passed_quizzes) / (total_items * student_count)) * 100,
                1,
            )

        course_cards.append({
            "id": str(c.id),
            "title": c.title,
            "description": c.description,
            "subject": c.subject,
            "grade_level": c.grade_level,
            "is_active": c.is_active,
            "chapter_count": chapter_count,
            "student_count": student_count,
            "avg_progress": avg_progress,
        })

    return {
        "total_courses": len(courses),
        "total_students": total_students,
        "upcoming_sessions": upcoming_sessions,
        "active_homework": active_homework,
        "courses": course_cards,
    }


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.COURSE_CREATE)),
):
    if not current_user.teacher_profile:
        raise HTTPException(status_code=400, detail="Teacher profile not found")
    course = await service.create_course(db, current_user.teacher_profile.id, data)

    # Notify all admins so they can review/validate the new course.
    admins_res = await db.execute(
        select(User.id).where(User.role == Role.ADMIN, User.is_active == True)
    )
    teacher_name = f"{current_user.first_name} {current_user.last_name}"
    for (admin_id,) in admins_res.all():
        await notif_service.create_notification(
            db,
            NotificationCreate(
                user_id=admin_id,
                title="Nouveau cours créé",
                message=f"{teacher_name} a créé le cours « {course.title} ».",
                type="info",
                link=f"/admin/courses/{course.id}/content",
            ),
        )

    return course


@router.get("/", response_model=list[CourseResponse])
async def list_courses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == Role.TEACHER and current_user.teacher_profile:
        courses = await service.get_courses(db, teacher_id=current_user.teacher_profile.id)
    else:
        courses = await service.get_courses(db)
    return courses


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = await service.get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: UUID,
    data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.COURSE_UPDATE)),
):
    course = await service.get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if current_user.role == Role.TEACHER and current_user.teacher_profile:
        if course.teacher_id != current_user.teacher_profile.id:
            raise HTTPException(status_code=403, detail="Not your course")
    course = await service.update_course(db, course, data)
    return course


# --- Sessions ---

@router.post("/{course_id}/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    course_id: UUID,
    data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.LIVE_CLASS_CREATE)),
):
    course = await service.get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    session = await service.create_session(db, course_id, data)
    return session


@router.get("/{course_id}/sessions", response_model=list[SessionResponse])
async def list_sessions(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await service.get_sessions_by_course(db, course_id)


# --- Enrollments ---

@router.post("/enroll", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def enroll(
    data: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    enrollment = await service.enroll_student(db, data.student_id, data.course_id)
    return enrollment


@router.get("/{course_id}/enrollments", response_model=list[EnrollmentResponse])
async def list_enrollments(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.COURSE_READ)),
):
    return await service.get_enrollments_by_course(db, course_id)
