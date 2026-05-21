import enum
from functools import wraps
from typing import Callable


class Role(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    VENDOR = "vendor"


class Permission(str, enum.Enum):
    # Users
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"

    # Courses
    COURSE_CREATE = "course:create"
    COURSE_READ = "course:read"
    COURSE_UPDATE = "course:update"
    COURSE_DELETE = "course:delete"

    # Live classes
    LIVE_CLASS_CREATE = "live_class:create"
    LIVE_CLASS_JOIN = "live_class:join"
    LIVE_CLASS_MANAGE = "live_class:manage"

    # Homework
    HOMEWORK_CREATE = "homework:create"
    HOMEWORK_SUBMIT = "homework:submit"
    HOMEWORK_GRADE = "homework:grade"
    HOMEWORK_READ = "homework:read"

    # Attendance
    ATTENDANCE_MANAGE = "attendance:manage"
    ATTENDANCE_VIEW = "attendance:view"

    # Recordings
    RECORDING_MANAGE = "recording:manage"
    RECORDING_VIEW = "recording:view"

    # Payments
    PAYMENT_MANAGE = "payment:manage"
    PAYMENT_VIEW = "payment:view"

    # Analytics
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_FULL = "analytics:full"

    # Admin
    ADMIN_FULL = "admin:full"

    # Vendor
    VENDOR_MANAGE_PRODUCTS = "vendor:manage_products"
    VENDOR_VIEW_SALES = "vendor:view_sales"


# Role → Permissions mapping
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: set(Permission),  # Admin has all permissions
    Role.TEACHER: {
        Permission.COURSE_CREATE,
        Permission.COURSE_READ,
        Permission.COURSE_UPDATE,
        Permission.LIVE_CLASS_CREATE,
        Permission.LIVE_CLASS_MANAGE,
        Permission.HOMEWORK_CREATE,
        Permission.HOMEWORK_GRADE,
        Permission.HOMEWORK_READ,
        Permission.ATTENDANCE_MANAGE,
        Permission.ATTENDANCE_VIEW,
        Permission.RECORDING_MANAGE,
        Permission.RECORDING_VIEW,
        Permission.ANALYTICS_VIEW,
        Permission.USER_READ,
    },
    Role.STUDENT: {
        Permission.COURSE_READ,
        Permission.LIVE_CLASS_JOIN,
        Permission.HOMEWORK_SUBMIT,
        Permission.HOMEWORK_READ,
        Permission.ATTENDANCE_VIEW,
        Permission.RECORDING_VIEW,
        Permission.PAYMENT_VIEW,
    },
    Role.VENDOR: {
        Permission.VENDOR_MANAGE_PRODUCTS,
        Permission.VENDOR_VIEW_SALES,
        Permission.COURSE_READ,
        Permission.USER_READ,
    },
}


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


def has_any_permission(role: Role, permissions: list[Permission]) -> bool:
    role_perms = ROLE_PERMISSIONS.get(role, set())
    return any(p in role_perms for p in permissions)
