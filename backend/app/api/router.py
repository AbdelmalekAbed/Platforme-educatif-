from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.courses import router as courses_router
from app.api.routes.homework import router as homework_router
from app.api.routes.attendance import router as attendance_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.payments import router as payments_router
from app.api.routes.admin import router as admin_router
from app.api.routes.content import router as content_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(courses_router)
api_router.include_router(homework_router)
api_router.include_router(attendance_router)
api_router.include_router(notifications_router)
api_router.include_router(payments_router)
api_router.include_router(admin_router)
api_router.include_router(content_router)
