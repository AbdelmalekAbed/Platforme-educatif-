from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import Base
from app.core.config import settings

# Import all models so Alembic sees them
from app.modules.users.models import User, StudentProfile, TeacherProfile, VendorProfile
from app.modules.courses.models import (
    Course, CourseSession, Enrollment, CourseResource, Subject,
    Chapter, ChapterResource, Quiz, QuizQuestion, QuizAttempt, ChapterResourceProgress,
)
from app.modules.attendance.models import Attendance
from app.modules.recordings.models import Recording
from app.modules.homework.models import Homework, HomeworkSubmission
from app.modules.payments.models import Payment, Invoice
from app.modules.notifications.models import Notification

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
