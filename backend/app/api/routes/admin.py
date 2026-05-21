from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from uuid import UUID
from app.core.database import get_db
from app.core.permissions import Role, Permission
from app.api.dependencies import get_current_user, require_role
from app.modules.users.models import User, StudentProfile, TeacherProfile
from app.modules.courses.models import Course, Enrollment, Subject
from app.modules.courses.schemas import SubjectCreate, SubjectResponse, CourseAdminCreate
from app.modules.payments.models import Payment
from app.modules.auth.schemas import UserResponse
from app.modules.notifications import service as notif_service
from app.modules.notifications.models import Notification
from app.modules.notifications.schemas import NotificationCreate

router = APIRouter(prefix="/admin", tags=["Admin"])


# --- Subjects ---

DEFAULT_SUBJECTS = [
    "Mathématiques", "Physique", "Chimie", "Biologie",
    "Sciences de la vie et de la Terre", "Français", "Arabe", "Anglais",
    "Histoire-Géographie", "Philosophie", "Informatique",
    "Économie", "Gestion", "Arts plastiques", "Éducation physique et sportive",
]


@router.get("/subjects", response_model=list[SubjectResponse])
async def list_subjects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(Subject).order_by(Subject.name))
    return result.scalars().all()


@router.post("/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    data: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    existing = await db.execute(select(Subject).where(Subject.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Cette matière existe déjà")
    subject = Subject(name=data.name)
    db.add(subject)
    await db.flush()
    await db.refresh(subject)
    return subject


@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(
    subject_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Matière introuvable")
    await db.delete(subject)


@router.put("/subjects/{subject_id}/toggle", response_model=SubjectResponse)
async def toggle_subject_active(
    subject_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Matière introuvable")
    subject.is_active = not subject.is_active
    await db.flush()
    await db.refresh(subject)
    return subject



@router.get("/stats")
async def get_platform_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    total_users = await db.execute(select(func.count(User.id)))
    total_students = await db.execute(select(func.count(StudentProfile.id)))
    total_teachers = await db.execute(select(func.count(TeacherProfile.id)))
    total_courses = await db.execute(select(func.count(Course.id)))
    total_enrollments = await db.execute(select(func.count(Enrollment.id)))
    total_revenue = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == "completed")
    )

    return {
        "total_users": total_users.scalar(),
        "total_students": total_students.scalar(),
        "total_teachers": total_teachers.scalar(),
        "total_courses": total_courses.scalar(),
        "total_enrollments": total_enrollments.scalar(),
        "total_revenue": float(total_revenue.scalar()),
    }


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    role: Role | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    query = select(User)
    if role:
        query = query.where(User.role == role)
    query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    await db.flush()
    return {"id": str(user.id), "is_active": user.is_active}


# --- Course Management ---

@router.get("/courses")
async def list_all_courses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(
        select(Course, TeacherProfile, User)
        .join(TeacherProfile, Course.teacher_id == TeacherProfile.id)
        .join(User, TeacherProfile.user_id == User.id)
        .order_by(Course.created_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": str(course.id),
            "title": course.title,
            "description": course.description,
            "subject": course.subject,
            "grade_level": course.grade_level,
            "max_students": course.max_students,
            "price": course.price,
            "is_active": course.is_active,
            "thumbnail_url": course.thumbnail_url,
            "created_at": course.created_at.isoformat(),
            "teacher_id": str(course.teacher_id),
            "teacher_name": f"{teacher_user.first_name} {teacher_user.last_name}",
            "teacher_email": teacher_user.email,
        }
        for course, _tp, teacher_user in rows
    ]


@router.post("/courses", status_code=status.HTTP_201_CREATED)
async def admin_create_course(
    data: CourseAdminCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    # Frontend sends User.id; resolve to the matching TeacherProfile.
    # Also accept a TeacherProfile.id directly for backward compatibility.
    result = await db.execute(
        select(TeacherProfile).where(TeacherProfile.user_id == data.teacher_id)
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        result = await db.execute(
            select(TeacherProfile).where(TeacherProfile.id == data.teacher_id)
        )
        teacher = result.scalar_one_or_none()
    if not teacher:
        # Auto-create a TeacherProfile if the user exists with TEACHER role
        user_result = await db.execute(
            select(User).where(User.id == data.teacher_id, User.role == Role.TEACHER)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Teacher profile not found")
        teacher = TeacherProfile(user_id=user.id)
        db.add(teacher)
        await db.flush()
        await db.refresh(teacher)
    course = Course(
        teacher_id=teacher.id,
        title=data.title,
        description=data.description,
        subject=data.subject,
        grade_level=data.grade_level,
        max_students=data.max_students,
        price=data.price,
    )
    db.add(course)
    await db.flush()
    await db.refresh(course)

    # Notify the assigned teacher that a new course has been created for them.
    await notif_service.create_notification(
        db,
        NotificationCreate(
            user_id=teacher.user_id,
            title="Nouveau cours assigné",
            message=f"L'administration vous a assigné le cours « {course.title} ».",
            type="info",
            link=f"/teacher/courses/{course.id}/content",
        ),
    )

    return {
        "id": str(course.id),
        "title": course.title,
        "description": course.description,
        "subject": course.subject,
        "grade_level": course.grade_level,
        "max_students": course.max_students,
        "price": course.price,
        "is_active": course.is_active,
        "teacher_id": str(course.teacher_id),
        "created_at": course.created_at.isoformat(),
    }


@router.put("/courses/{course_id}/toggle")
async def admin_toggle_course_active(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course.is_active = not course.is_active
    await db.flush()
    return {"id": str(course.id), "is_active": course.is_active}


@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    # Clean up notifications whose link points to this course so users don't end
    # up clicking dead links.
    await db.execute(
        delete(Notification).where(Notification.link.contains(f"/courses/{course_id}"))
    )
    await db.delete(course)
