"""Routes for course content: chapters, resources, quizzes.

Flat hierarchy: Course → Chapter → (Resource | Quiz) directly.
"""
import re
import uuid as _uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, true as sql_true
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.permissions import Role
from app.core.security.media_tokens import sign_media_url
from app.api.dependencies import get_current_user, require_role
from app.modules.users.models import User, TeacherProfile
from app.modules.courses.models import (
    Course, Chapter, ChapterResource, Quiz, QuizQuestion,
    QuizAttempt, ChapterResourceProgress,
    StudentCourseKnown, StudentChapterKnown,
)
from app.modules.courses.content_schemas import (
    ChapterCreate, ChapterUpdate, ChapterResponse,
    ChapterResourceCreate, ChapterResourceUpdate, ChapterResourceResponse,
    QuizCreate, QuizUpdate, QuizResponse, QuizStudentResponse,
    QuizQuestionCreate, QuizQuestionResponse,
    QuizAttemptSubmit, QuizAttemptResponse,
    ChapterReorderRequest, ChapterItemsReorderRequest, QuizQuestionsReorderRequest,
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Receive a PDF/video/image file and return a public URL plus inferred kind.

    The video size limit comes from platform_settings.courses.video_max_size_mb
    (admin-configurable). Non-video files keep the hard 500 MB cap.
    """
    filename = file.filename or "file"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extension non supportée: .{ext}. Autorisées: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    kind = ALLOWED_EXTENSIONS[ext]
    max_bytes = MAX_UPLOAD_BYTES
    if kind == "video":
        from app.modules.settings import service as settings_service
        courses_settings = await settings_service.get_section(db, "courses")
        max_bytes = courses_settings.video_max_size_mb * 1024 * 1024
    max_mb = max_bytes // (1024 * 1024)

    safe_base = _SAFE_NAME_RE.sub("_", filename.rsplit(".", 1)[0])[:80] or "file"
    stored_name = f"{_uuid.uuid4().hex}_{safe_base}.{ext}"
    dest = UPLOAD_DIR / stored_name

    written = 0
    with dest.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            written += len(chunk)
            if written > max_bytes:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"Fichier trop volumineux (max {max_mb} Mo)",
                )
            out.write(chunk)

    return {
        "url": f"/uploads/{stored_name}",
        "kind": kind,
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
    current_user: User = Depends(require_role(Role.ADMIN)),
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
    current_user: User = Depends(require_role(Role.ADMIN)),
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
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapitre introuvable")
    await db.delete(chapter)


@router.patch("/courses/{course_id}/chapters/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_chapters(
    course_id: UUID,
    payload: ChapterReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Apply a new ordering for all chapters in a course.

    Each chapter's position is set to its index in `payload.chapter_ids`. The list
    must contain exactly the chapters that currently belong to the course (same set,
    new order) — otherwise we reject to prevent partial moves that leave gaps.
    """
    course_res = await db.execute(select(Course).where(Course.id == course_id))
    if not course_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Cours introuvable")

    chapters_res = await db.execute(
        select(Chapter).where(Chapter.course_id == course_id)
    )
    chapters = chapters_res.scalars().all()
    existing_ids = {c.id for c in chapters}
    requested_ids = list(payload.chapter_ids)

    if len(requested_ids) != len(set(requested_ids)):
        raise HTTPException(status_code=400, detail="Doublons dans la liste de chapitres")
    if set(requested_ids) != existing_ids:
        raise HTTPException(
            status_code=400,
            detail="La liste doit contenir exactement les chapitres existants du cours",
        )

    chapter_by_id = {c.id: c for c in chapters}
    for idx, cid in enumerate(requested_ids):
        chapter_by_id[cid].position = idx
    await db.flush()


# =====================================================================
# Chapter items (flat list of resources + quizzes, ordered by position)
# =====================================================================

async def _chapter_items_payload(
    db: AsyncSession,
    chapter: Chapter,
    student_id: UUID | None,
    force_completed: bool = False,
) -> list[dict]:
    """Build the unified item list (resources + quizzes) for a chapter.

    When `force_completed` is True (chapter or parent course marked as "known"
    by the student), every item is reported as completed regardless of actual
    visit history.
    """
    completed_resource_ids: set[UUID] = set()
    passed_quiz_ids: set[UUID] = set()
    if student_id is not None and not force_completed:
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
            "url": sign_media_url(r.url),
            "duration_seconds": r.duration_seconds,
            "position": r.position,
            "is_completed": force_completed or r.id in completed_resource_ids,
        })
    for q in chapter.quizzes:
        items.append({
            "item_type": "quiz",
            "id": str(q.id),
            "title": q.title,
            "pass_score": q.pass_score,
            "position": q.position,
            "question_count": len(q.questions),
            "is_completed": force_completed or q.id in passed_quiz_ids,
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


@router.patch("/chapters/{chapter_id}/items/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_chapter_items(
    chapter_id: UUID,
    payload: ChapterItemsReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Apply a new unified ordering for resources and quizzes in a chapter.

    Resources and quizzes share a single `position` sequence; the position assigned
    to each item is its index in `payload.items`. The list must contain exactly the
    items currently in the chapter (same multiset, new order).
    """
    chapter_res = await db.execute(
        select(Chapter)
        .options(selectinload(Chapter.resources), selectinload(Chapter.quizzes))
        .where(Chapter.id == chapter_id)
    )
    chapter = chapter_res.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapitre introuvable")

    existing = {("resource", r.id): r for r in chapter.resources}
    existing.update({("quiz", q.id): q for q in chapter.quizzes})

    requested = [(e.type, e.id) for e in payload.items]
    if len(requested) != len(set(requested)):
        raise HTTPException(status_code=400, detail="Doublons dans la liste d'items")
    if set(requested) != set(existing.keys()):
        raise HTTPException(
            status_code=400,
            detail="La liste doit contenir exactement les items du chapitre",
        )

    for idx, key in enumerate(requested):
        existing[key].position = idx
    await db.flush()


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
    current_user: User = Depends(require_role(Role.ADMIN)),
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
    current_user: User = Depends(require_role(Role.ADMIN)),
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
    current_user: User = Depends(require_role(Role.ADMIN)),
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
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    chapter_res = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    if not chapter_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Chapitre introuvable")

    pass_score = data.pass_score
    if pass_score is None:
        from app.modules.settings import service as settings_service
        courses_settings = await settings_service.get_section(db, "courses")
        pass_score = courses_settings.default_pass_score

    quiz = Quiz(
        chapter_id=chapter_id,
        title=data.title,
        instructions=data.instructions,
        pass_score=pass_score,
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
    current_user: User = Depends(require_role(Role.ADMIN)),
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
    current_user: User = Depends(require_role(Role.ADMIN)),
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
    current_user: User = Depends(require_role(Role.ADMIN)),
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
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(QuizQuestion).where(QuizQuestion.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question introuvable")
    await db.delete(question)


@router.patch("/quizzes/{quiz_id}/questions/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_quiz_questions(
    quiz_id: UUID,
    payload: QuizQuestionsReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Apply a new ordering for all questions in a quiz."""
    quiz_res = await db.execute(
        select(Quiz).options(selectinload(Quiz.questions)).where(Quiz.id == quiz_id)
    )
    quiz = quiz_res.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz introuvable")

    existing_ids = {q.id for q in quiz.questions}
    requested_ids = list(payload.question_ids)
    if len(requested_ids) != len(set(requested_ids)):
        raise HTTPException(status_code=400, detail="Doublons dans la liste de questions")
    if set(requested_ids) != existing_ids:
        raise HTTPException(
            status_code=400,
            detail="La liste doit contenir exactement les questions du quiz",
        )

    question_by_id = {q.id: q for q in quiz.questions}
    for idx, qid in enumerate(requested_ids):
        question_by_id[qid].position = idx
    await db.flush()


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
# Student "known" marks (course / chapter shortcuts to 100% progress)
# =====================================================================

@router.post("/courses/{course_id}/known", status_code=status.HTTP_204_NO_CONTENT)
async def mark_course_known(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.STUDENT)),
):
    if not current_user.student_profile:
        raise HTTPException(status_code=400, detail="Profil étudiant manquant")
    course_res = await db.execute(select(Course.id).where(Course.id == course_id))
    if not course_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Cours introuvable")
    student_id = current_user.student_profile.id
    if not await _is_course_known(db, course_id, student_id):
        db.add(StudentCourseKnown(student_id=student_id, course_id=course_id))
        await db.flush()


@router.delete("/courses/{course_id}/known", status_code=status.HTTP_204_NO_CONTENT)
async def unmark_course_known(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.STUDENT)),
):
    if not current_user.student_profile:
        raise HTTPException(status_code=400, detail="Profil étudiant manquant")
    res = await db.execute(
        select(StudentCourseKnown).where(
            StudentCourseKnown.course_id == course_id,
            StudentCourseKnown.student_id == current_user.student_profile.id,
        )
    )
    row = res.scalar_one_or_none()
    if row is not None:
        await db.delete(row)
        await db.flush()


@router.post("/chapters/{chapter_id}/known", status_code=status.HTTP_204_NO_CONTENT)
async def mark_chapter_known(
    chapter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.STUDENT)),
):
    if not current_user.student_profile:
        raise HTTPException(status_code=400, detail="Profil étudiant manquant")
    chapter_res = await db.execute(select(Chapter.id).where(Chapter.id == chapter_id))
    if not chapter_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Chapitre introuvable")
    student_id = current_user.student_profile.id
    exists_res = await db.execute(
        select(StudentChapterKnown.id).where(
            StudentChapterKnown.chapter_id == chapter_id,
            StudentChapterKnown.student_id == student_id,
        )
    )
    if exists_res.scalar_one_or_none() is None:
        db.add(StudentChapterKnown(student_id=student_id, chapter_id=chapter_id))
        await db.flush()


@router.delete("/chapters/{chapter_id}/known", status_code=status.HTTP_204_NO_CONTENT)
async def unmark_chapter_known(
    chapter_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.STUDENT)),
):
    if not current_user.student_profile:
        raise HTTPException(status_code=400, detail="Profil étudiant manquant")
    res = await db.execute(
        select(StudentChapterKnown).where(
            StudentChapterKnown.chapter_id == chapter_id,
            StudentChapterKnown.student_id == current_user.student_profile.id,
        )
    )
    row = res.scalar_one_or_none()
    if row is not None:
        await db.delete(row)
        await db.flush()


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


async def _is_course_known(db: AsyncSession, course_id: UUID, student_id: UUID) -> bool:
    res = await db.execute(
        select(StudentCourseKnown.id)
        .where(
            StudentCourseKnown.course_id == course_id,
            StudentCourseKnown.student_id == student_id,
        )
        .limit(1)
    )
    return res.scalar_one_or_none() is not None


async def _known_chapter_ids_for_course(
    db: AsyncSession, course_id: UUID, student_id: UUID
) -> set[UUID]:
    res = await db.execute(
        select(StudentChapterKnown.chapter_id)
        .join(Chapter, StudentChapterKnown.chapter_id == Chapter.id)
        .where(
            Chapter.course_id == course_id,
            StudentChapterKnown.student_id == student_id,
        )
    )
    return {row[0] for row in res.all()}


async def _course_progress_percent(
    db: AsyncSession,
    course_id: UUID,
    student_id: UUID,
) -> float:
    """Compute progress = completed items / total items for a student in a course.

    A course or chapter marked as "known" by the student forces its items to
    count as completed, even with no actual visit history.
    """
    if await _is_course_known(db, course_id, student_id):
        return 100.0

    # Count items per chapter so chapters marked "known" can contribute their full weight.
    res_per_chapter = await db.execute(
        select(
            Chapter.id,
            func.count(func.distinct(ChapterResource.id)),
            func.count(func.distinct(Quiz.id)),
        )
        .select_from(Chapter)
        .outerjoin(ChapterResource, ChapterResource.chapter_id == Chapter.id)
        .outerjoin(Quiz, Quiz.chapter_id == Chapter.id)
        .where(Chapter.course_id == course_id)
        .group_by(Chapter.id)
    )
    chapter_totals = {ch_id: r_count + q_count for ch_id, r_count, q_count in res_per_chapter.all()}
    total = sum(chapter_totals.values())
    if total == 0:
        return 0.0

    known_chapter_ids = await _known_chapter_ids_for_course(db, course_id, student_id)
    completed_from_known = sum(chapter_totals.get(ch_id, 0) for ch_id in known_chapter_ids)

    # For chapters NOT marked known, count actual visited resources + passed quizzes.
    completed_res = await db.execute(
        select(func.count(ChapterResourceProgress.id))
        .join(ChapterResource, ChapterResourceProgress.resource_id == ChapterResource.id)
        .join(Chapter, ChapterResource.chapter_id == Chapter.id)
        .where(
            Chapter.course_id == course_id,
            ChapterResourceProgress.student_id == student_id,
            ChapterResourceProgress.is_completed.is_(True),
            Chapter.id.notin_(known_chapter_ids) if known_chapter_ids else sql_true(),
        )
    )
    completed_resources = completed_res.scalar() or 0

    passed_qz_res = await db.execute(
        select(func.count(func.distinct(Quiz.id)))
        .join(Chapter, Quiz.chapter_id == Chapter.id)
        .join(QuizAttempt, QuizAttempt.quiz_id == Quiz.id)
        .where(
            Chapter.course_id == course_id,
            QuizAttempt.student_id == student_id,
            QuizAttempt.score >= Quiz.pass_score,
            Chapter.id.notin_(known_chapter_ids) if known_chapter_ids else sql_true(),
        )
    )
    passed_quizzes = passed_qz_res.scalar() or 0

    completed = completed_from_known + completed_resources + passed_quizzes
    return round((min(completed, total) / total) * 100, 1)


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
        is_known = False
        if current_user.role == Role.STUDENT and current_user.student_profile:
            sp_id = current_user.student_profile.id
            is_known = await _is_course_known(db, course.id, sp_id)
            progress_percent = await _course_progress_percent(db, course.id, sp_id)

        courses.append({
            "id": str(course.id),
            "title": course.title,
            "description": course.description,
            "subject": course.subject,
            "grade_level": course.grade_level,
            "thumbnail_url": sign_media_url(course.thumbnail_url),
            "teacher_id": str(course.teacher_id),
            "teacher_name": f"{teacher_user.first_name} {teacher_user.last_name}",
            "created_at": course.created_at.isoformat(),
            "progress_percent": progress_percent,
            "is_known": is_known,
            "is_active": course.is_active,
        })

    # Level-wide progress: average of all matching courses' progress for this student.
    level_progress_percent = 0.0
    if current_user.role == Role.STUDENT and current_user.student_profile and total > 0:
        all_ids_res = await db.execute(select(Course.id).where(*base_filters))
        all_course_ids = [row[0] for row in all_ids_res.all()]
        if all_course_ids:
            sp_id = current_user.student_profile.id
            per_course = [
                await _course_progress_percent(db, cid, sp_id) for cid in all_course_ids
            ]
            level_progress_percent = round(sum(per_course) / len(per_course), 1)

    return {
        "items": courses,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + len(courses) < total,
        "level_progress_percent": level_progress_percent,
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
    course_known = False
    known_chapter_ids: set[UUID] = set()
    if current_user.role == Role.STUDENT and current_user.student_profile:
        student_id = current_user.student_profile.id
        course_known = await _is_course_known(db, course_id, student_id)
        known_chapter_ids = await _known_chapter_ids_for_course(db, course_id, student_id)
        progress_percent = await _course_progress_percent(db, course_id, student_id)

    chapters_out = []
    for c in chapters:
        chapter_known = c.id in known_chapter_ids
        items = await _chapter_items_payload(
            db, c, student_id, force_completed=course_known or chapter_known
        )
        chapters_out.append({
            "id": str(c.id),
            "title": c.title,
            "description": c.description,
            "position": c.position,
            "items_count": len(items),
            "items": items,
            "is_known": chapter_known,
        })

    return {
        "id": str(course.id),
        "title": course.title,
        "description": course.description,
        "subject": course.subject,
        "grade_level": course.grade_level,
        "thumbnail_url": sign_media_url(course.thumbnail_url),
        "teacher_id": str(course.teacher_id),
        "teacher_name": f"{teacher_user.first_name} {teacher_user.last_name}",
        "progress_percent": progress_percent,
        "is_known": course_known,
        "chapters": chapters_out,
    }
