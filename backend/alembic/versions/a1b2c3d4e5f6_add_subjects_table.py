"""add subjects table

Revision ID: a1b2c3d4e5f6
Revises: f7a9cb70b998
Create Date: 2026-05-14 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f7a9cb70b998'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_SUBJECTS = [
    "Mathématiques", "Physique", "Chimie", "Biologie",
    "Sciences de la vie et de la Terre", "Français", "Arabe", "Anglais",
    "Histoire-Géographie", "Philosophie", "Informatique",
    "Économie", "Gestion", "Arts plastiques", "Éducation physique et sportive",
]


def upgrade() -> None:
    subjects_table = op.create_table(
        'subjects',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    import uuid
    from datetime import datetime, timezone

    op.bulk_insert(
        subjects_table,
        [
            {
                "id": str(uuid.uuid4()),
                "name": name,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
            }
            for name in DEFAULT_SUBJECTS
        ],
    )


def downgrade() -> None:
    op.drop_table('subjects')
