"""student profile refresh: add school/parent fields, create parent_contacts + notif_prefs

Adds the new student profile columns (school_level, school_name, city,
preferred_language, gender), creates the parent_contacts and parent_notif_prefs
tables, and backfills:
  - school_level from the legacy grade_level column
  - parent_contacts from the legacy parent_name/parent_phone/parent_email columns
    (only when parent_email is present; rows without parent_email are skipped)

Legacy columns (grade_level, parent_name, parent_phone, parent_email) are
intentionally kept by this migration so the backfill can be validated. They are
dropped by a follow-up migration (d2e3f4a5b6c7).

Revision ID: d1e2f3a4b5c6
Revises: c8d4f1e9a302
Create Date: 2026-05-17 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c8d4f1e9a302'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PARENT_RELATION_VALUES = ('pere', 'mere', 'tuteur_legal', 'autre')
NOTIF_CHANNEL_VALUES = ('email', 'sms', 'both')


def _column_exists(conn, table: str, column: str) -> bool:
    row = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    ).first()
    return row is not None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Nouvelles colonnes sur student_profiles (idempotent — tolère une exécution partielle antérieure)
    if not _column_exists(conn, 'student_profiles', 'school_level'):
        op.add_column('student_profiles', sa.Column('school_level', sa.String(length=50), nullable=True))
    if not _column_exists(conn, 'student_profiles', 'school_name'):
        op.add_column('student_profiles', sa.Column('school_name', sa.String(length=200), nullable=True))
    if not _column_exists(conn, 'student_profiles', 'city'):
        op.add_column('student_profiles', sa.Column('city', sa.String(length=100), nullable=True))
    if not _column_exists(conn, 'student_profiles', 'preferred_language'):
        op.add_column(
            'student_profiles',
            sa.Column('preferred_language', sa.String(length=10), nullable=True, server_default='fr'),
        )
    if not _column_exists(conn, 'student_profiles', 'gender'):
        op.add_column('student_profiles', sa.Column('gender', sa.String(length=20), nullable=True))

    # Backfill school_level <- grade_level
    op.execute(
        "UPDATE student_profiles SET school_level = grade_level "
        "WHERE grade_level IS NOT NULL AND school_level IS NULL"
    )

    # 2. Nettoyage défensif : si une exécution antérieure a partiellement créé des
    # objets (tables ou enums), on les drop avant de recréer. Aucune perte de
    # donnée — le backfill (étape 5) est rejoué.
    op.execute("DROP TABLE IF EXISTS parent_notif_prefs CASCADE")
    op.execute("DROP TABLE IF EXISTS parent_contacts CASCADE")
    op.execute("DROP TYPE IF EXISTS notif_channel")
    op.execute("DROP TYPE IF EXISTS parent_relation")

    # 3. Table parent_contacts — les enums seront créés automatiquement par
    # op.create_table à la première rencontre de la colonne typée.

    op.create_table(
        'parent_contacts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=False),
        sa.Column(
            'relation',
            sa.Enum(*PARENT_RELATION_VALUES, name='parent_relation'),
            nullable=False,
        ),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('profession', sa.String(length=200), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('verification_token_hash', sa.String(length=64), nullable=True),
        sa.Column('verification_token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('verification_token_hash', name='uq_parent_contacts_token_hash'),
    )
    op.create_index('ix_parent_contacts_student_id', 'parent_contacts', ['student_id'])
    op.create_index('ix_parent_contacts_email', 'parent_contacts', ['email'])
    # Contrainte métier : au plus un contact "primaire" par élève
    op.create_index(
        'uq_parent_contacts_primary_per_student',
        'parent_contacts',
        ['student_id'],
        unique=True,
        postgresql_where=sa.text('is_primary = true'),
    )

    # 4. Table parent_notif_prefs (1:1 avec parent_contacts)
    op.create_table(
        'parent_notif_prefs',
        sa.Column('parent_id', sa.UUID(), nullable=False),
        sa.Column('invoices', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('absences', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('grades', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('reports', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('reminders', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            'channel',
            sa.Enum(*NOTIF_CHANNEL_VALUES, name='notif_channel'),
            nullable=False,
            server_default='email',
        ),
        sa.ForeignKeyConstraint(['parent_id'], ['parent_contacts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('parent_id'),
    )

    # 5. Backfill parent_contacts depuis les colonnes plates legacy
    # Stratégie : pour chaque student_profile avec parent_email NON NULL, créer
    # un ParentContact (relation=autre, is_primary=true, is_verified=false) +
    # ses ParentNotifPrefs par défaut. Les élèves sans parent_email sont skip.
    import uuid
    from datetime import datetime, timezone

    conn = op.get_bind()
    legacy_rows = conn.execute(sa.text(
        "SELECT id, parent_name, parent_phone, parent_email FROM student_profiles "
        "WHERE parent_email IS NOT NULL AND TRIM(parent_email) <> ''"
    )).fetchall()

    now = datetime.now(timezone.utc)
    for row in legacy_rows:
        contact_id = uuid.uuid4()
        full_name = (row.parent_name or '').strip() or 'Contact parental'
        conn.execute(
            sa.text(
                "INSERT INTO parent_contacts ("
                "id, student_id, full_name, relation, phone, email, "
                "is_verified, is_primary, created_at, updated_at"
                ") VALUES ("
                ":id, :sid, :name, 'autre', :phone, :email, false, true, :now, :now)"
            ),
            {
                "id": contact_id,
                "sid": row.id,
                "name": full_name,
                "phone": row.parent_phone,
                "email": row.parent_email.strip(),
                "now": now,
            },
        )
        conn.execute(
            sa.text(
                "INSERT INTO parent_notif_prefs ("
                "parent_id, invoices, absences, grades, reports, reminders, channel"
                ") VALUES (:pid, true, true, true, true, true, 'email')"
            ),
            {"pid": contact_id},
        )


def downgrade() -> None:
    op.drop_table('parent_notif_prefs')
    op.drop_index('uq_parent_contacts_primary_per_student', table_name='parent_contacts')
    op.drop_index('ix_parent_contacts_email', table_name='parent_contacts')
    op.drop_index('ix_parent_contacts_student_id', table_name='parent_contacts')
    op.drop_table('parent_contacts')

    sa.Enum(name='notif_channel').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='parent_relation').drop(op.get_bind(), checkfirst=True)

    op.drop_column('student_profiles', 'gender')
    op.drop_column('student_profiles', 'preferred_language')
    op.drop_column('student_profiles', 'city')
    op.drop_column('student_profiles', 'school_name')
    op.drop_column('student_profiles', 'school_level')
