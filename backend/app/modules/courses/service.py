import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.courses.models import Course, CourseSession, Enrollment
from app.modules.courses.schemas import CourseCreate, CourseUpdate, SessionCreate


async def create_course(db: AsyncSession, teacher_profile_id, data: CourseCreate) -> Course:
    course = Course(
        teacher_id=teacher_profile_id,
        title=data.title,
        description=data.description,
        subject=data.subject,
        grade_level=data.grade_level,
        max_students=data.max_students,
        price=data.price,
    )
    db.add(course)
    await db.flush()
    return course


async def get_courses(db: AsyncSession, teacher_id=None, is_active=True):
    query = select(Course).where(Course.is_active == is_active)
    if teacher_id:
        query = query.where(Course.teacher_id == teacher_id)
    result = await db.execute(query)
    return result.scalars().all()


async def get_course_by_id(db: AsyncSession, course_id) -> Course | None:
    result = await db.execute(select(Course).where(Course.id == course_id))
    return result.scalar_one_or_none()


async def update_course(db: AsyncSession, course: Course, data: CourseUpdate) -> Course:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(course, key, value)
    await db.flush()
    return course


async def create_session(db: AsyncSession, course_id, data: SessionCreate) -> CourseSession:
    session = CourseSession(
        course_id=course_id,
        title=data.title,
        description=data.description,
        scheduled_at=data.scheduled_at,
        duration_minutes=data.duration_minutes,
        room_id=str(uuid.uuid4()),
    )
    db.add(session)
    await db.flush()
    return session


async def get_sessions_by_course(db: AsyncSession, course_id):
    result = await db.execute(
        select(CourseSession).where(CourseSession.course_id == course_id).order_by(CourseSession.scheduled_at)
    )
    return result.scalars().all()


async def get_session_by_id(db: AsyncSession, session_id) -> CourseSession | None:
    result = await db.execute(select(CourseSession).where(CourseSession.id == session_id))
    return result.scalar_one_or_none()


async def enroll_student(db: AsyncSession, student_id, course_id) -> Enrollment:
    enrollment = Enrollment(student_id=student_id, course_id=course_id)
    db.add(enrollment)
    await db.flush()
    return enrollment


async def get_enrollments_by_student(db: AsyncSession, student_id):
    result = await db.execute(
        select(Enrollment).where(Enrollment.student_id == student_id)
    )
    return result.scalars().all()


async def get_enrollments_by_course(db: AsyncSession, course_id):
    result = await db.execute(
        select(Enrollment).where(Enrollment.course_id == course_id)
    )
    return result.scalars().all()
