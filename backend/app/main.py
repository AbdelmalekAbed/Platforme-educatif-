from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.router import api_router
from app.websocket.endpoints import router as ws_router

# Import all models so SQLAlchemy can resolve string-based relationships
from app.modules.users.models import User, StudentProfile, TeacherProfile, VendorProfile  # noqa: F401
from app.modules.users.parent_models import ParentContact, ParentNotifPrefs  # noqa: F401
from app.modules.courses.models import Course, CourseSession, Enrollment, CourseResource  # noqa: F401
from app.modules.recordings.models import Recording  # noqa: F401
from app.modules.attendance.models import Attendance  # noqa: F401
from app.modules.homework.models import Homework, HomeworkSubmission  # noqa: F401
from app.modules.notifications.models import Notification  # noqa: F401
from app.modules.payments.models import Payment, Invoice  # noqa: F401


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Workaround: Next.js Turbopack rewrites strip the trailing slash, so
    # /api/v1/courses/ from the browser arrives here as /api/v1/courses.
    # FastAPI's default response would be a 307 redirect to the slash version,
    # but the browser's fetch() drops the Authorization header on that redirect
    # and the next hop fails with 403 "Not authenticated".
    # We patch the scope before routing so the index routes match directly.
    INDEX_PATHS_NEEDING_SLASH = {
        "/api/v1/courses",
        "/api/v1/homework",
        "/api/v1/payments",
        "/api/v1/notifications",
    }

    @app.middleware("http")
    async def add_trailing_slash_for_index(request, call_next):
        path = request.url.path
        if path in INDEX_PATHS_NEEDING_SLASH:
            new_path = path + "/"
            request.scope["path"] = new_path
            request.scope["raw_path"] = new_path.encode()
        return await call_next(request)

    # REST API routes
    app.include_router(api_router)

    # WebSocket routes
    app.include_router(ws_router)

    # Static uploads (PDFs/videos uploaded by admins/teachers)
    upload_dir = Path(__file__).resolve().parent.parent / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": settings.APP_VERSION}

    return app


app = create_app()
