"""Routes for course content: chapters, resources, quizzes.

Flat hierarchy: Course → Chapter → (Resource | Quiz) directly.
"""
import re
import uuid as _uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.permissions import Role
from app.api.dependencies import get_current_user, require_role
from app.modules.users.models import User, TeacherProfile
from app.modules.courses.models import (
    Course, Chapter, ChapterResource, Quiz, QuizQuestion,
    QuizAttempt, ChapterResourceProgress,
)
from app.modules.courses.content_schemas import (
    ChapterCreate, ChapterUpdate, ChapterResponse,
    ChapterResourceCreate, ChapterResourceUpdate, ChapterResourceResponse,
    QuizCreate, QuizUpdate, QuizResponse, QuizStudentResponse,
    QuizQuestionCreate, QuizQuestionResponse,
    QuizAttemptSubmit, QuizAttemptResponse,
)


router = APIRouter(prefix="/content", tags=["Content"])


# Local file storage for PDFs/videos uploaded by admins/teachers.
UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    "pdf": "pdf",
    "mp4": "video", "webm": "video", "mov": "video", "mkv": "video", "avi": "video",
    "png": "image", "jpg": "image", "jpeg": "image", "gif": "image", "webp": "image",
}
MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500 MB
_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


@router.post("/uploads", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    """Receive a PDF/video/image file and return a public URL plus inferred kind."""
    filename = file.filename or "file"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extension non supportée: .{ext}. Autorisées: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    safe_base = _SAFE_NAME_RE.sub("_", filename.rsplit(".", 1)[0])[:80] or "file"
    stored_name = f"{_uuid.uuid4().hex}_{safe_base}.{ext}"
    dest = UPLOAD_DIR / stored_name

    written = 0
    with dest.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            written += len(chunk)
            if written > MAX_UPLOAD_BYTES:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 500 Mo)")
            out.write(chunk)

    return {
        "url": f"/uploads/{stored_name}",
        "kind": ALLOWED_EXTENSIONS[ext],
        "filename": filename,
        "size": written,
    }


# =====================================================================
# Chapters
# =====================================================================

@router.get("/courses/{course_id}/chapters", response_model=list[ChapterResponse])
async def list_chapters(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Chapter)
        .where(Chapter.course_id == course_id)
        .order_by(Chapter.position, Chapter.created_at)
    )
    return result.scalars().all()


@router.post("/courses/{course_id}/chapters", response_model=ChapterResponse, status_code=status.HTTP_201_CREATED)
async def create_chapter(
    course_id: UUID,
    data: ChapterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable")
    chapter = Chapter(
        course_id=course_id,
        title=data.title,
        description=data.description,
        position=data.position,
    )
    db.add(chapter)
    await db.flush()
    await db.refresh(chapter)
    return chapter


@router.put("/chapters/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(
    chapter_id: UUID,
    data: ChapterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapitre introuvable")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(chapter, key, value)
    await db.flush()
    await db.refresh(chapter)
    return chapter


@router.delete("/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chapter(
    chapter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapitre introuvable")
    await db.delete(chapter)


# =====================================================================
# Chapter items (flat list of resources + quizzes, ordered by position)
# =====================================================================

async def _chapter_items_payload(
    db: AsyncSession,
    chapter: Chapter,
    student_id: UUID | None,
) -> list[dict]:
    """Build the unified item list (resources + quizzes) for a chapter."""
    completed_resource_ids: set[UUID] = set()
    passed_quiz_ids: set[UUID] = set()
    if student_id is not None:
        cr_res = await db.execute(
            select(ChapterResourceProgress.resource_id)
            .join(ChapterResource, ChapterResourceProgress.resource_id == ChapterResource.id)
            .where(
                ChapterResource.chapter_id == chapter.id,
                ChapterResourceProgress.student_id == student_id,
                ChapterResourceProgress.is_completed.is_(True),
            )
        )
        completed_resource_ids = {row[0] for row in cr_res.all()}

        # Quiz is "completed" if student has any attempt meeting pass_score
        attempts_res = await db.execute(
            select(QuizAttempt.quiz_id, QuizAttempt.score, Quiz.pass_score)
            .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
            .where(
                Quiz.chapter_id == chapter.id,
                QuizAttempt.student_id == student_id,
            )
        )
        for quiz_id, score, pass_score in attempts_res.all():
            if score is not None and pass_score is not None and score >= pass_score:
                passed_quiz_ids.add(quiz_id)

    items: list[dict] = []
    for r in chapter.resources:
        items.append({
            "item_type": "resource",
            "id": str(r.id),
            "title": r.title,
            "kind": r.kind,
            "url": r.url,
            "duration_seconds": r.duration_seconds,
            "position": r.position,
            "is_completed": r.id in completed_resource_ids,
        })
    for q in chapter.quizzes:
        items.append({
            "item_type": "quiz",
            "id": str(q.id),
            "title": q.title,
            "pass_score": q.pass_score,
            "position": q.position,
            "question_count": len(q.questions),
            "is_completed": q.id in passed_quiz_ids,
        })
    items.sort(key=lambda i: i["position"])
    return items


@router.get("/chapters/{chapter_id}")
async def get_chapter_with_items(
    chapter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Chapter)
        .options(
            selectinload(Chapter.resources),
            selectinload(Chapter.quizzes).selectinload(Quiz.questions),
        )
        .where(Chapter.id == chapter_id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapitre introuvable")

    student_id = None
    if current_user.role == Role.STUDENT and current_user.student_profile:
        student_id = current_user.student_profile.id

    items = await _chapter_items_payload(db, chapter, student_id)
    return {
        "id": str(chapter.id),
        "course_id": str(chapter.course_id),
        "title": chapter.title,
        "description": chapter.description,
        "position": chapter.position,
        "items_count": len(items),
        "items": items,
    }


# =====================================================================
# Chapter Resources
# =====================================================================

@router.get("/chapters/{chapter_id}/resources", response_model=list[ChapterResourceResponse])
async def list_resources(
    chapter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChapterResource)
        .where(ChapterResource.chapter_id == chapter_id)
        .order_by(ChapterResource.position, ChapterResource.created_at)
    )
    return result.scalars().all()


@router.post("/chapters/{chapter_id}/resources", response_model=ChapterResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    chapter_id: UUID,
    data: ChapterResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    chapter_res = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    if not chapter_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Chapitre introuvable")
    resource = ChapterResource(
        chapter_id=chapter_id,
        title=data.title,
        kind=data.kind,
        url=data.url,
        duration_seconds=data.duration_seconds,
        position=data.position,
    )
    db.add(resource)
    await db.flush()
    await db.refresh(resource)
    return resource


@router.put("/resources/{resource_id}", response_model=ChapterResourceResponse)
async def update_resource(
    resource_id: UUID,
    data: ChapterResourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    result = await db.execute(select(ChapterResource).where(ChapterResource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Ressource introuvable")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(resource, key, value)
    await db.flush()
    await db.refresh(resource)
    return resource


@router.delete("/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    result = await db.execute(select(ChapterResource).where(ChapterResource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Ressource introuvable")
    await db.delete(resource)


@router.post("/resources/{resource_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
async def mark_resource_completed(
    resource_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.STUDENT)),
):
    """Student marks a resource as visited/completed."""
    if not current_user.student_profile:
        raise HTTPException(status_code=400, detail="Profil étudiant manquant")
    res = await db.execute(select(ChapterResource).where(ChapterResource.id == resource_id))
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Ressource introuvable")

    prog_res = await db.execute(
        select(ChapterResourceProgress).where(
            ChapterResourceProgress.student_id == current_user.student_profile.id,
            ChapterResourceProgress.resource_id == resource_id,
        )
    )
    progress = prog_res.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if progress:
        progress.is_completed = True
        progress.completed_at = now
    else:
        db.add(ChapterResourceProgress(
            student_id=current_user.student_profile.id,
            resource_id=resource_id,
            is_completed=True,
            visited_at=now,
            completed_at=now,
        ))
    await db.flush()


# =====================================================================
# Quiz management (admin/teacher)
# =====================================================================

@router.post("/chapters/{chapter_id}/quizzes", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    chapter_id: UUID,
    data: QuizCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    chapter_res = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    if not chapter_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Chapitre introuvable")

    quiz = Quiz(
        chapter_id=chapter_id,
        title=data.title,
        instructions=data.instructions,
        pass_score=data.pass_score,
        position=data.position,
    )
    db.add(quiz)
    await db.flush()
    await db.refresh(quiz)
    return QuizResponse(
        id=quiz.id,
        chapter_id=quiz.chapter_id,
        title=quiz.title,
        instructions=quiz.instructions,
        pass_score=quiz.pass_score,
        position=quiz.position,
        questions=[],
    )


@router.get("/quizzes/{quiz_id}", response_model=QuizResponse)
async def get_quiz_admin(
    quiz_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    result = await db.execute(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.id == quiz_id)
    )
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz introuvable")
    return quiz


@router.put("/quizzes/{quiz_id}", response_model=QuizResponse)
async def update_quiz(
    quiz_id: UUID,
    data: QuizUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    result = await db.execute(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.id == quiz_id)
    )
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz introuvable")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(quiz, key, value)
    await db.flush()
    await db.refresh(quiz)
    return quiz


@router.delete("/quizzes/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    quiz_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz introuvable")
    await db.delete(quiz)


@router.post("/quizzes/{quiz_id}/questions", response_model=QuizQuestionResponse, status_code=status.HTTP_201_CREATED)
async def add_quiz_question(
    quiz_id: UUID,
    data: QuizQuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    quiz_res = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    if not quiz_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Quiz introuvable")
    if not any(c.id == data.correct_choice_id for c in data.choices):
        raise HTTPException(status_code=400, detail="correct_choice_id ne correspond à aucun choix")
    question = QuizQuestion(
        quiz_id=quiz_id,
        text=data.text,
        choices=[c.model_dump() for c in data.choices],
        correct_choice_id=data.correct_choice_id,
        explanation=data.explanation,
        points=data.points,
        position=data.position,
    )
    db.add(question)
    await db.flush()
    await db.refresh(question)
    return question


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz_question(
    question_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    result = await db.execute(select(QuizQuestion).where(QuizQuestion.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question introuvable")
    await db.delete(question)


# =====================================================================
# Quiz student access
# =====================================================================

@router.get("/quizzes/{quiz_id}/take", response_model=QuizStudentResponse)
async def get_quiz_for_student(
    quiz_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.id == quiz_id)
    )
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz introuvable")
    return QuizStudentResponse(
        id=quiz.id,
        chapter_id=quiz.chapter_id,
        title=quiz.title,
        instructions=quiz.instructions,
        pass_score=quiz.pass_score,
        position=quiz.position,
        questions=[
            {
                "id": q.id,
                "text": q.text,
                "choices": q.choices,
                "points": q.points,
                "position": q.position,
            }
            for q in quiz.questions
        ],
    )


@router.post("/quizzes/{quiz_id}/submit", response_model=QuizAttemptResponse)
async def submit_quiz(
    quiz_id: UUID,
    data: QuizAttemptSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.STUDENT)),
):
    if not current_user.student_profile:
        raise HTTPException(status_code=400, detail="Profil étudiant manquant")

    result = await db.execute(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.id == quiz_id)
    )
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz introuvable")

    questions_by_id = {q.id: q for q in quiz.questions}
    answers_payload = []
    correct_count = 0
    total_points = 0.0
    earned_points = 0.0

    for ans in data.answers:
        q = questions_by_id.get(ans.question_id)
        if not q:
            continue
        is_correct = ans.choice_id == q.correct_choice_id
        if is_correct:
            correct_count += 1
            earned_points += q.points
        total_points += q.points
        answers_payload.append({
            "question_id": str(ans.question_id),
            "choice_id": ans.choice_id,
            "is_correct": is_correct,
        })

    score = (earned_points / total_points * 100.0) if total_points > 0 else 0.0

    attempt = QuizAttempt(
        quiz_id=quiz_id,
        student_id=current_user.student_profile.id,
        score=score,
        correct_count=correct_count,
        total_count=len(quiz.questions),
        answers=answers_payload,
    )
    db.add(attempt)
    await db.flush()
    await db.refresh(attempt)
    return attempt


@router.get("/quizzes/{quiz_id}/my-attempts", response_model=list[QuizAttemptResponse])
async def my_quiz_attempts(
    quiz_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.STUDENT)),
):
    if not current_user.student_profile:
        return []
    result = await db.execute(
        select(QuizAttempt)
        .where(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.student_id == current_user.student_profile.id,
        )
        .order_by(QuizAttempt.completed_at.desc())
    )
    return result.scalars().all()


# =====================================================================
# Student catalogs
# =====================================================================

@router.get("/levels")
async def list_levels(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return supported grade levels with course counts, scoped by role.

    - student: only active courses
    - teacher: only the teacher's own courses (any status)
    - admin: all courses (any status)
    """
    levels = ["6eme", "5eme", "4eme", "3eme"]
    labels = {"6eme": "6ème", "5eme": "5ème", "4eme": "4ème", "3eme": "3ème"}
    out = []
    for level in levels:
        query = select(func.count(Course.id)).where(Course.grade_level == level)
        if current_user.role == Role.TEACHER and current_user.teacher_profile:
            query = query.where(Course.teacher_id == current_user.teacher_profile.id)
        elif current_user.role == Role.ADMIN:
            pass  # all courses, no extra filter
        else:
            query = query.where(Course.is_active == True)
        count_res = await db.execute(query)
        out.append({
            "code": level,
            "label": labels[level],
            "course_count": count_res.scalar() or 0,
        })
    return out


async def _course_progress_percent(
    db: AsyncSession,
    course_id: UUID,
    student_id: UUID,
) -> float:
    """Compute progress = completed items / total items for a student in a course."""
    # Total items = resources + quizzes across all chapters
    total_res = await db.execute(
        select(func.count(ChapterResource.id))
        .join(Chapter, ChapterResource.chapter_id == Chapter.id)
        .where(Chapter.course_id == course_id)
    )
    total_resources = total_res.scalar() or 0

    total_qz = await db.execute(
        select(func.count(Quiz.id))
        .join(Chapter, Quiz.chapter_id == Chapter.id)
        .where(Chapter.course_id == course_id)
    )
    total_quizzes = total_qz.scalar() or 0

    total = total_resources + total_quizzes
    if total == 0:
        return 0.0

    completed_res = await db.execute(
        select(func.count(ChapterResourceProgress.id))
        .join(ChapterResource, ChapterResourceProgress.resource_id == ChapterResource.id)
        .join(Chapter, ChapterResource.chapter_id == Chapter.id)
        .where(
            Chapter.course_id == course_id,
            ChapterResourceProgress.student_id == student_id,
            ChapterResourceProgress.is_completed.is_(True),
        )
    )
    completed_resources = completed_res.scalar() or 0

    # Count quizzes the student has passed (at least one attempt with score >= pass_score)
    passed_qz_res = await db.execute(
        select(func.count(func.distinct(Quiz.id)))
        .join(Chapter, Quiz.chapter_id == Chapter.id)
        .join(QuizAttempt, QuizAttempt.quiz_id == Quiz.id)
        .where(
            Chapter.course_id == course_id,
            QuizAttempt.student_id == student_id,
            QuizAttempt.score >= Quiz.pass_score,
        )
    )
    passed_quizzes = passed_qz_res.scalar() or 0

    completed = completed_resources + passed_quizzes
    return round((completed / total) * 100, 1)


@router.get("/levels/{level}/courses")
async def list_courses_by_level(
    level: str,
    skip: int = 0,
    limit: int = 4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns paginated courses for a given grade level, scoped by role.

    - student: only active courses
    - teacher: only the teacher's own courses (any status)
    - admin: all courses (any status)
    """
    base_filters = [Course.grade_level == level]
    if current_user.role == Role.TEACHER and current_user.teacher_profile:
        base_filters.append(Course.teacher_id == current_user.teacher_profile.id)
    elif current_user.role != Role.ADMIN:
        base_filters.append(Course.is_active == True)

    count_res = await db.execute(
        select(func.count(Course.id)).where(*base_filters)
    )
    total = count_res.scalar() or 0

    result = await db.execute(
        select(Course, TeacherProfile, User)
        .join(TeacherProfile, Course.teacher_id == TeacherProfile.id)
        .join(User, TeacherProfile.user_id == User.id)
        .where(*base_filters)
        .order_by(Course.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = result.all()
    courses = []
    for course, _tp, teacher_user in rows:
        progress_percent = 0.0
        if current_user.role == Role.STUDENT and current_user.student_profile:
            progress_percent = await _course_progress_percent(
                db, course.id, current_user.student_profile.id
            )

        courses.append({
            "id": str(course.id),
            "title": course.title,
            "description": course.description,
            "subject": course.subject,
            "grade_level": course.grade_level,
            "thumbnail_url": course.thumbnail_url,
            "teacher_id": str(course.teacher_id),
            "teacher_name": f"{teacher_user.first_name} {teacher_user.last_name}",
            "created_at": course.created_at.isoformat(),
            "progress_percent": progress_percent,
            "is_active": course.is_active,
        })

    return {
        "items": courses,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + len(courses) < total,
    }


@router.get("/courses/{course_id}/full")
async def get_course_full(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns a course with all its chapters and flat item lists."""
    result = await db.execute(
        select(Course, TeacherProfile, User)
        .join(TeacherProfile, Course.teacher_id == TeacherProfile.id)
        .join(User, TeacherProfile.user_id == User.id)
        .where(Course.id == course_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Cours introuvable")
    course, _tp, teacher_user = row

    chapters_res = await db.execute(
        select(Chapter)
        .options(
            selectinload(Chapter.resources),
            selectinload(Chapter.quizzes).selectinload(Quiz.questions),
        )
        .where(Chapter.course_id == course_id)
        .order_by(Chapter.position, Chapter.created_at)
    )
    chapters = chapters_res.scalars().all()

    student_id = None
    progress_percent = 0.0
    if current_user.role == Role.STUDENT and current_user.student_profile:
        student_id = current_user.student_profile.id
        progress_percent = await _course_progress_percent(db, course_id, student_id)

    chapters_out = []
    for c in chapters:
        items = await _chapter_items_payload(db, c, student_id)
        chapters_out.append({
            "id": str(c.id),
            "title": c.title,
            "description": c.description,
            "position": c.position,
            "items_count": len(items),
            "items": items,
        })

    return {
        "id": str(course.id),
        "title": course.title,
        "description": course.description,
        "subject": course.subject,
        "grade_level": course.grade_level,
        "thumbnail_url": course.thumbnail_url,
        "teacher_id": str(course.teacher_id),
        "teacher_name": f"{teacher_user.first_name} {teacher_user.last_name}",
        "progress_percent": progress_percent,
        "chapters": chapters_out,
    }
