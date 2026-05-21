"""drop legacy student_profiles columns (grade_level, parent_name/phone/email)

À EXÉCUTER UNIQUEMENT après validation du backfill effectué par la migration
d1e2f3a4b5c6. Vérifier au préalable :

    SELECT COUNT(*) FROM student_profiles WHERE parent_email IS NOT NULL;
    SELECT COUNT(*) FROM parent_contacts;
    -- les deux doivent correspondre (au cas par cas pour les emails vides).

    SELECT COUNT(*) FROM student_profiles WHERE grade_level IS NOT NULL;
    SELECT COUNT(*) FROM student_profiles WHERE school_level IS NOT NULL;

Cette migration est destructive : elle supprime définitivement les colonnes
legacy. Le downgrade les recrée vides — les données perdues ne sont PAS
restaurées (le backfill inverse n'est pas implémenté car parent_contacts est
le nouveau référentiel).

Revision ID: d2e3f4a5b6c7
Revises: d1e2f3a4b5c6
Create Date: 2026-05-17 12:05:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('student_profiles', 'parent_email')
    op.drop_column('student_profiles', 'parent_phone')
    op.drop_column('student_profiles', 'parent_name')
    op.drop_column('student_profiles', 'grade_level')


def downgrade() -> None:
    op.add_column('student_profiles', sa.Column('grade_level', sa.String(length=50), nullable=True))
    op.add_column('student_profiles', sa.Column('parent_name', sa.String(length=200), nullable=True))
    op.add_column('student_profiles', sa.Column('parent_phone', sa.String(length=20), nullable=True))
    op.add_column('student_profiles', sa.Column('parent_email', sa.String(length=255), nullable=True))
