#!/usr/bin/env python
"""
Crée un compte admin par défaut dans la base de données.

Usage:
    python scripts/db/seed_admin.py
    python scripts/db/seed_admin.py --db-url postgresql://user:pass@host/db
"""
import sys
import argparse
import uuid
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path: scripts/db/ -> scripts/ -> project root -> backend/
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))


def seed_admin(db_url_override: str = None) -> bool:
    print("🔐 Création du compte admin...")
    print("-" * 60)

    try:
        from sqlalchemy import create_engine, text
        from app.core.security import hash_password
        from app.core.config import settings
        from app.core.permissions import Role

        db_url = db_url_override or settings.DATABASE_URL_SYNC
        engine = create_engine(db_url)

        admin_id = str(uuid.uuid4())
        admin_email = "admin@edtech.com"
        admin_password = "Admin123456"
        hashed_password = hash_password(admin_password)
        admin_role_db = Role.ADMIN.name        # stored as enum name in DB
        admin_role_display = Role.ADMIN.value
        now = datetime.now(timezone.utc)

        sql = text("""
            INSERT INTO users (
                id, email, hashed_password, first_name, last_name,
                phone, role, is_active, is_verified, created_at, updated_at
            ) VALUES (
                :id, :email, :hashed_password, :first_name, :last_name,
                :phone, :role, true, true, :created_at, :updated_at
            ) ON CONFLICT (email) DO NOTHING;
        """)

        with engine.connect() as conn:
            result = conn.execute(sql, {
                "id": admin_id,
                "email": admin_email,
                "hashed_password": hashed_password,
                "first_name": "Admin",
                "last_name": "Platform",
                "phone": "+1234567890",
                "role": admin_role_db,
                "created_at": now,
                "updated_at": now,
            })
            conn.commit()

        if result.rowcount > 0:
            print("✅ Compte admin créé avec succès!")
        else:
            print("ℹ️  Compte admin déjà présent dans la base de données.")

        print("-" * 60)
        print("📋 Informations de connexion:")
        print(f"   Email    : {admin_email}")
        print(f"   Password : {admin_password}")
        print(f"   Rôle     : {admin_role_display}")
        print("-" * 60)
        print("🌐 Accès:")
        print("   Frontend : http://localhost:3000")
        print("   API Docs : http://localhost:8000/docs")
        print("-" * 60)
        return True

    except ImportError as e:
        print(f"❌ Erreur d'importation: {e}")
        print("\n💡 Assurez-vous que:")
        print("   1. Vous êtes dans le répertoire racine du projet")
        print("   2. Les dépendances backend sont installées (venv activé)")
        return False

    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("\n💡 Assurez-vous que:")
        print("   1. PostgreSQL est en cours d'exécution")
        print("   2. La base 'edtech' existe")
        print("   3. Les migrations ont été appliquées (alembic upgrade head)")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Créer un compte admin par défaut")
    parser.add_argument("--db-url", help="URL de la base de données (optionnel, surcharge settings)")
    args = parser.parse_args()

    success = seed_admin(db_url_override=args.db_url)
    sys.exit(0 if success else 1)
