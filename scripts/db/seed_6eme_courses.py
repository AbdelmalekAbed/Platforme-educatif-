#!/usr/bin/env python
"""Importe / prépare l'arborescence des cours de 6ème (dossier `cours/6ème/`).

Mapping dossier → base :

    cours/6ème/<MATIÈRE>/<N. Notion>/6eme*.pdf
                │           │            └── ChapterResource (Cours / Fiche / Correction)
                │           └── Chapter   (titre = notion sans le préfixe "N. ")
                └── Course  (titre = matière en casse propre, grade_level="6eme")

- **Toutes** les matières (sous-dossiers directs de `6ème/`) deviennent des cours,
  **même vides** (0 chapitre pour l'instant).
- **Toutes** les notions (sous-dossiers d'une matière) deviennent des chapitres,
  **même sans PDF `6eme`** (chapitre vide, prêt à recevoir son contenu plus tard).
- Seuls les PDF dont le nom commence par `6eme` deviennent des ressources
  (kinds `pdf`/`fiche`/`correction`). Ils sont copiés dans `backend/uploads/` et
  servis via `/uploads/<nom>`.

IDEMPOTENT (upsert) — rejouable sans rien casser :
- cours identifié par (grade_level, titre) ; chapitre par (course_id, titre) ;
  ressource par (chapter_id, kind).
- ce qui existe déjà n'est PAS recréé ni recopié (la progression élève est
  préservée). Quand tu ajoutes plus tard des PDF `6eme` dans une notion, relancer
  le script crée uniquement les ressources manquantes.
- `--replace` (optionnel, destructif) supprime d'abord tout le contenu 6ème avant
  de reconstruire. À éviter une fois que des élèves ont de la progression.

⚠️  Lit `backend/.env` → base **Neon partagée** (le script force le CWD vers
    `backend/`). Cf. CLAUDE.md (piège `.env` relatif au CWD).

Usage :
    python scripts/db/seed_6eme_courses.py            # upsert
    python scripts/db/seed_6eme_courses.py --dry-run  # aperçu, n'écrit rien
    python scripts/db/seed_6eme_courses.py --replace  # reconstruction complète
"""
import argparse
import re
import shutil
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_PATH = PROJECT_ROOT / "backend"
UPLOAD_DIR = BACKEND_PATH / "uploads"
sys.path.insert(0, str(BACKEND_PATH))

# Même assainissement de nom que l'endpoint d'upload (content.py).
_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")
_NOTION_PREFIX_RE = re.compile(r"^\s*(\d+)\s*\.\s*(.+?)\s*$")

SUBJECT = "Mathématiques"
GRADE_LEVEL = "6eme"


def pretty_course_title(folder_name: str) -> str:
    """ARITHMÉTIQUES -> Arithmétiques ; GÉOMÉTRIE DE BASE -> Géométrie de base."""
    return folder_name.strip().capitalize()


def parse_notion(folder_name: str) -> tuple[int, str]:
    """'1. Multiples et diviseurs' -> (1, 'Multiples et diviseurs')."""
    m = _NOTION_PREFIX_RE.match(folder_name)
    if m:
        return int(m.group(1)), m.group(2).strip()
    return 999, folder_name.strip()


def classify_pdf(filename: str) -> tuple[str, str, int]:
    """Retourne (kind, titre, position) selon le nom du PDF."""
    stem = filename[:-4] if filename.lower().endswith(".pdf") else filename
    if "CORRECTION" in stem.upper():
        return "correction", "Correction", 2
    if filename.startswith("6eme_fiche_"):
        return "fiche", "Fiche d'exercices", 1
    return "pdf", "Cours", 0


def find_source_root() -> Path:
    """Le seul sous-dossier de `cours/` (évite tout souci d'encodage de « 6ème »)."""
    cours_dir = PROJECT_ROOT / "cours"
    if not cours_dir.is_dir():
        raise FileNotFoundError(f"Dossier introuvable : {cours_dir}")
    subdirs = [p for p in cours_dir.iterdir() if p.is_dir()]
    if not subdirs:
        raise FileNotFoundError(f"Aucun sous-dossier dans {cours_dir}")
    if len(subdirs) > 1:
        sixth = [p for p in subdirs if p.name.startswith("6")]
        if sixth:
            return sixth[0]
    return subdirs[0]


def _visible_dirs(parent: Path) -> list[Path]:
    return [p for p in parent.iterdir()
            if p.is_dir() and p.name != "_check" and not p.name.startswith(".")]


def collect_structure(source_root: Path) -> list[dict]:
    """[{title, chapters:[{num, title, pdfs:[Path]}]}] — TOUTES matières/notions,
    y compris vides (matière sans notion → 0 chapitre ; notion sans PDF 6eme → 0 ressource)."""
    courses = []
    for matiere in sorted(_visible_dirs(source_root), key=lambda p: p.name):
        chapters = []
        for notion in sorted(_visible_dirs(matiere), key=lambda p: parse_notion(p.name)[0]):
            pdfs = sorted(
                f for f in notion.iterdir()
                if f.is_file() and f.name.startswith("6eme") and f.suffix.lower() == ".pdf"
            )
            num, title = parse_notion(notion.name)
            chapters.append({"num": num, "title": title, "pdfs": pdfs})
        courses.append({"title": pretty_course_title(matiere.name), "chapters": chapters})
    return courses


def store_pdf(src: Path, dry_run: bool) -> str:
    """Copie le PDF dans uploads/ et retourne l'URL `/uploads/<nom>`."""
    safe_base = _SAFE_NAME_RE.sub("_", src.stem)[:80] or "file"
    stored = f"{uuid.uuid4().hex}_{safe_base}.pdf"
    if not dry_run:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, UPLOAD_DIR / stored)
    return f"/uploads/{stored}"


def main(dry_run: bool, replace: bool) -> int:
    mode = "DRY-RUN" if dry_run else ("REPLACE" if replace else "UPSERT")
    print(f"📚 Import / préparation des cours de 6ème  [{mode}]")
    print("-" * 64)

    # ⚠️ `Settings` lit `.env` RELATIVEMENT au CWD. Le backend tourne depuis
    # `backend/` → backend/.env (Neon). On force le CWD avant d'importer la config,
    # sinon on retombe sur les defaults localhost:5432 (mauvaise base).
    import os
    os.chdir(BACKEND_PATH)

    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session
    from app.core.config import settings
    from app.modules.users.models import User, StudentProfile, TeacherProfile, VendorProfile  # noqa: F401
    from app.modules.users.parent_models import ParentContact, ParentNotifPrefs  # noqa: F401
    from app.modules.courses.models import (  # noqa: F401
        Subject, Course, CourseSession, Enrollment, CourseResource,
        Chapter, ChapterResource, Quiz, QuizQuestion, QuizAttempt,
        ChapterResourceProgress, StudentCourseKnown, StudentChapterKnown,
    )
    from app.modules.recordings.models import Recording  # noqa: F401
    from app.modules.attendance.models import Attendance  # noqa: F401
    from app.modules.homework.models import Homework, HomeworkSubmission  # noqa: F401
    from app.modules.notifications.models import Notification  # noqa: F401
    from app.modules.payments.models import Payment, Invoice  # noqa: F401

    source_root = find_source_root()
    print(f"Source : {source_root}")
    structure = collect_structure(source_root)
    n_courses = len(structure)
    n_chapters = sum(len(c["chapters"]) for c in structure)
    n_pdfs = sum(len(ch["pdfs"]) for c in structure for ch in c["chapters"])
    print(f"Arborescence : {n_courses} cours, {n_chapters} chapitres, {n_pdfs} PDF 6eme")
    for c in structure:
        empties = sum(1 for ch in c["chapters"] if not ch["pdfs"])
        tag = "  (cours vide)" if not c["chapters"] else (f"  ({empties} chap. vide(s))" if empties else "")
        print(f"  • {c['title']} — {len(c['chapters'])} chapitre(s){tag}")

    engine = create_engine(settings.DATABASE_URL_SYNC)
    with Session(engine) as session:
        teacher = session.scalars(select(TeacherProfile)).first()
        if teacher is None:
            print("❌ Aucun enseignant en base — impossible de rattacher les cours.")
            return 1

        if replace:
            existing = session.scalars(
                select(Course).where(Course.grade_level == GRADE_LEVEL)
            ).all()
            if existing:
                print(f"\n🗑️  --replace : suppression de {len(existing)} cours 6ème (cascade) :")
                for c in existing:
                    print(f"     - {c.title}")
                    session.delete(c)
                session.flush()

        stats = dict(courses_new=0, chapters_new=0, resources_new=0, files=0, resources_skip=0)
        now = datetime.now(timezone.utc)
        print("\n➝  Synchronisation :")
        for idx, c in enumerate(structure):
            # created_at décroissant selon l'ordre (alphabétique) des matières →
            # ordre d'affichage stable dans le catalogue (tri created_at DESC).
            course_dt = now - timedelta(minutes=idx)
            course = session.scalars(
                select(Course).where(Course.grade_level == GRADE_LEVEL, Course.title == c["title"])
            ).first()
            if course is None:
                course = Course(
                    teacher_id=teacher.id,
                    title=c["title"],
                    description=f"Cours de mathématiques 6ème — {c['title']}.",
                    subject=SUBJECT,
                    grade_level=GRADE_LEVEL,
                    price=0,
                    is_active=True,
                    created_at=course_dt,
                    updated_at=course_dt,
                )
                session.add(course)
                stats["courses_new"] += 1
                flag = "＋ cours"
            else:
                course.created_at = course_dt  # garde l'ordre stable
                flag = "= cours"
            session.flush()
            print(f"  {flag} : {c['title']}")

            for ch in c["chapters"]:
                chapter = session.scalars(
                    select(Chapter).where(Chapter.course_id == course.id, Chapter.title == ch["title"])
                ).first()
                if chapter is None:
                    chapter = Chapter(
                        course_id=course.id,
                        title=ch["title"],
                        position=ch["num"],
                        created_at=course_dt,
                    )
                    session.add(chapter)
                    stats["chapters_new"] += 1
                    ch_flag = "＋"
                else:
                    chapter.position = ch["num"]
                    ch_flag = "="
                session.flush()

                resources = sorted((classify_pdf(p.name) + (p,) for p in ch["pdfs"]),
                                   key=lambda t: t[2])
                added = []
                for kind, title, position, src in resources:
                    exists = session.scalars(
                        select(ChapterResource).where(
                            ChapterResource.chapter_id == chapter.id,
                            ChapterResource.kind == kind,
                        )
                    ).first()
                    if exists is not None:
                        stats["resources_skip"] += 1
                        continue
                    url = store_pdf(src, dry_run)
                    stats["files"] += 1
                    session.add(ChapterResource(
                        chapter_id=chapter.id, title=title, kind=kind,
                        url=url, position=position, created_at=course_dt,
                    ))
                    stats["resources_new"] += 1
                    added.append(title)
                detail = f"  →  ＋{', '.join(added)}" if added else ("  (vide)" if not ch["pdfs"] else "  (déjà présent)")
                print(f"      {ch_flag} {ch['title']}{detail}")

        if dry_run:
            print("\n🟡 DRY-RUN : rien écrit, aucun fichier copié.")
            session.rollback()
        else:
            session.commit()
            print("\n✅ Terminé.")
        print(f"   Cours créés       : {stats['courses_new']}")
        print(f"   Chapitres créés   : {stats['chapters_new']}")
        print(f"   Ressources créées : {stats['resources_new']} ({stats['files']} PDF copiés)")
        print(f"   Ressources déjà présentes (ignorées) : {stats['resources_skip']}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importer / préparer les cours de 6ème (idempotent)")
    parser.add_argument("--dry-run", action="store_true", help="N'écrit rien (aperçu)")
    parser.add_argument("--replace", action="store_true",
                        help="DESTRUCTIF : supprime tout le contenu 6ème avant de reconstruire")
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run, replace=args.replace))
