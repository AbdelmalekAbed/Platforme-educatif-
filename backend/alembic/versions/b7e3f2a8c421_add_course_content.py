"""add course content (chapters, notions, resources, quizzes)

Revision ID: b7e3f2a8c421
Revises: a1b2c3d4e5f6
Create Date: 2026-05-15 09:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'b7e3f2a8c421'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'chapters',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('course_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chapters_course_id', 'chapters', ['course_id'])

    op.create_table(
        'notions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('chapter_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notions_chapter_id', 'notions', ['chapter_id'])

    op.create_table(
        'notion_resources',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('notion_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('kind', sa.String(length=30), nullable=False),
        sa.Column('url', sa.String(length=1000), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['notion_id'], ['notions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notion_resources_notion_id', 'notion_resources', ['notion_id'])

    op.create_table(
        'quizzes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('notion_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('pass_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['notion_id'], ['notions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('notion_id'),
    )

    op.create_table(
        'quiz_questions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('quiz_id', sa.UUID(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('choices', sa.JSON(), nullable=False),
        sa.Column('correct_choice_id', sa.String(length=20), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('points', sa.Float(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_quiz_questions_quiz_id', 'quiz_questions', ['quiz_id'])

    op.create_table(
        'quiz_attempts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('quiz_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('correct_count', sa.Integer(), nullable=True),
        sa.Column('total_count', sa.Integer(), nullable=True),
        sa.Column('answers', sa.JSON(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_quiz_attempts_quiz_id', 'quiz_attempts', ['quiz_id'])
    op.create_index('ix_quiz_attempts_student_id', 'quiz_attempts', ['student_id'])

    op.create_table(
        'notion_progress',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('notion_id', sa.UUID(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.Column('visited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['notion_id'], ['notions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'notion_id', name='uq_notion_progress_student_notion'),
    )


def downgrade() -> None:
    op.drop_table('notion_progress')
    op.drop_index('ix_quiz_attempts_student_id', table_name='quiz_attempts')
    op.drop_index('ix_quiz_attempts_quiz_id', table_name='quiz_attempts')
    op.drop_table('quiz_attempts')
    op.drop_index('ix_quiz_questions_quiz_id', table_name='quiz_questions')
    op.drop_table('quiz_questions')
    op.drop_table('quizzes')
    op.drop_index('ix_notion_resources_notion_id', table_name='notion_resources')
    op.drop_table('notion_resources')
    op.drop_index('ix_notions_chapter_id', table_name='notions')
    op.drop_table('notions')
    op.drop_index('ix_chapters_course_id', table_name='chapters')
    op.drop_table('chapters')
