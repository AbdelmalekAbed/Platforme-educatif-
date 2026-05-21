from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.modules.users.models import User, StudentProfile, TeacherProfile, VendorProfile
from app.core.security import hash_password, verify_password
from app.core.permissions import Role
from app.modules.auth.schemas import RegisterRequest


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id) -> User | None:
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.student_profile),
            selectinload(User.teacher_profile),
            selectinload(User.vendor_profile),
        )
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, data: RegisterRequest) -> User:
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        role=data.role,
    )
    db.add(user)
    await db.flush()

    # Create role-specific profile
    if data.role == Role.STUDENT:
        db.add(StudentProfile(user_id=user.id))
    elif data.role == Role.TEACHER:
        db.add(TeacherProfile(user_id=user.id))
    elif data.role == Role.VENDOR:
        db.add(VendorProfile(user_id=user.id))

    await db.flush()
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
