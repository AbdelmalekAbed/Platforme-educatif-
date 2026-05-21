#!/usr/bin/env python
"""
Diagnostic DB: liste les utilisateurs, teacher_profiles, courses et leurs liens.

Usage:
    python scripts/db/diagnose.py
"""
import sys
from pathlib import Path

# Add backend to path: scripts/db/ -> scripts/ -> project root -> backend/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from sqlalchemy import create_engine, text


def main():
    from app.core.config import settings

    engine = create_engine(settings.DATABASE_URL_SYNC)

    with engine.connect() as conn:
        print("=" * 70)
        print("USERS")
        print("=" * 70)
        rows = conn.execute(text(
            "SELECT id, email, role, is_active FROM users ORDER BY role, email"
        )).fetchall()
        for r in rows:
            print(f"  {r.role:8} | {r.email:35} | active={r.is_active} | id={r.id}")

        print()
        print("=" * 70)
        print("TEACHER_PROFILES (linked to users)")
        print("=" * 70)
        rows = conn.execute(text(
            "SELECT tp.id AS profile_id, u.email, u.id AS user_id "
            "FROM teacher_profiles tp JOIN users u ON u.id = tp.user_id"
        )).fetchall()
        if not rows:
            print("  (aucun teacher_profile)")
        for r in rows:
            print(f"  profile_id={r.profile_id} | user={r.email} | user_id={r.user_id}")

        print()
        print("=" * 70)
        print("COURSES (with teacher info)")
        print("=" * 70)
        rows = conn.execute(text(
            "SELECT c.id, c.title, c.teacher_id AS profile_id, u.email AS teacher_email "
            "FROM courses c "
            "LEFT JOIN teacher_profiles tp ON tp.id = c.teacher_id "
            "LEFT JOIN users u ON u.id = tp.user_id "
            "ORDER BY c.created_at DESC"
        )).fetchall()
        if not rows:
            print("  (aucun cours)")
        for r in rows:
            print(f"  {r.title:30} | teacher_profile_id={r.profile_id} | teacher_email={r.teacher_email}")

        print()
        print("=" * 70)
        print("USERS WITH role=TEACHER BUT NO teacher_profile")
        print("=" * 70)
        rows = conn.execute(text(
            "SELECT u.id, u.email FROM users u "
            "LEFT JOIN teacher_profiles tp ON tp.user_id = u.id "
            "WHERE u.role = 'TEACHER' AND tp.id IS NULL"
        )).fetchall()
        if not rows:
            print("  (aucun — tous les profs ont un profil, OK)")
        for r in rows:
            print(f"  ⚠️  {r.email} (user_id={r.id}) n'a pas de teacher_profile")


if __name__ == "__main__":
    main()
