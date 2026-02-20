"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Video Jobs table
    op.create_table(
        "video_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("input_path", sa.String(1024), nullable=False),
        sa.Column("output_path", sa.String(1024), nullable=True),
        sa.Column("audio_path", sa.String(1024), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "uploading",
                "extracting_audio",
                "transcribing",
                "analyzing",
                "generating_edit_plan",
                "editing",
                "rendering",
                "completed",
                "failed",
                name="jobstatus",
            ),
            default="pending",
        ),
        sa.Column("pipeline_type", sa.String(128), default="cleaner"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("duration_seconds", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Transcript Chunks table
    op.create_table(
        "transcript_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            UUID(as_uuid=True),
            sa.ForeignKey("video_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("start_time", sa.Float, nullable=False),
        sa.Column("end_time", sa.Float, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("word_count", sa.Integer, default=0),
        sa.Column("is_filler", sa.Boolean, default=False),
        sa.Column("clarity_score", sa.Float, nullable=True),
        sa.Column("engagement_score", sa.Float, nullable=True),
        sa.Column("filler_score", sa.Float, nullable=True),
        sa.Column("retention_risk_score", sa.Float, nullable=True),
    )
    op.create_index("ix_transcript_chunks_job_id", "transcript_chunks", ["job_id"])

    # Edit Plans table
    op.create_table(
        "edit_plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            UUID(as_uuid=True),
            sa.ForeignKey("video_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("start_time", sa.Float, nullable=False),
        sa.Column("end_time", sa.Float, nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("source", sa.String(64), default="local"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_edit_plans_job_id", "edit_plans", ["job_id"])

    # Pipeline Configs table
    op.create_table(
        "pipeline_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(256), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("pipeline_type", sa.String(128), nullable=False),
        sa.Column("steps", JSON, default={}),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )


def downgrade():
    op.drop_table("pipeline_configs")
    op.drop_table("edit_plans")
    op.drop_table("transcript_chunks")
    op.drop_table("video_jobs")
    op.execute("DROP TYPE IF EXISTS jobstatus")
