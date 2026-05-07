"""Initial schema — users, features, jira_issues, pull_requests, mappings, metrics, workflow_runs.

Revision ID: 001
Revises: None
Create Date: 2026-02-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("developer", "admin", name="userrole"), default="developer"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Features ───────────────────────────────────────────────────────────
    op.create_table(
        "features",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("parent_id", sa.Integer, sa.ForeignKey("features.id"), nullable=True),
        sa.Column("defect_count", sa.Integer, default=0),
        sa.Column("health_score", sa.Float, default=100.0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Jira Issues ────────────────────────────────────────────────────────
    op.create_table(
        "jira_issues",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("jira_key", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("issue_type", sa.Enum("epic", "story", "task", "defect", "sub_task", name="jiraissuetype"), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.Enum("open", "in_progress", "in_review", "resolved", "closed", "reopened", name="jirastatus"), default="open"),
        sa.Column("priority", sa.String(50), nullable=True),
        sa.Column("severity", sa.String(50), nullable=True),
        sa.Column("assignee_email", sa.String(255), nullable=True),
        sa.Column("reporter_email", sa.String(255), nullable=True),
        sa.Column("parent_key", sa.String(50), nullable=True, index=True),
        sa.Column("epic_key", sa.String(50), nullable=True, index=True),
        sa.Column("resolution", sa.String(100), nullable=True),
        sa.Column("resolution_notes", sa.Text, nullable=True),
        sa.Column("reopen_count", sa.Integer, default=0),
        sa.Column("resolution_time_hours", sa.Float, nullable=True),
        sa.Column("labels", sa.Text, nullable=True),
        sa.Column("components", sa.Text, nullable=True),
        sa.Column("jira_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("jira_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Pull Requests ──────────────────────────────────────────────────────
    op.create_table(
        "pull_requests",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("pr_number", sa.Integer, nullable=False, index=True),
        sa.Column("repo", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.Enum("open", "merged", "closed", name="prstatus"), default="open"),
        sa.Column("author_email", sa.String(255), nullable=True),
        sa.Column("author_login", sa.String(255), nullable=True),
        sa.Column("files_changed", sa.Integer, default=0),
        sa.Column("additions", sa.Integer, default=0),
        sa.Column("deletions", sa.Integer, default=0),
        sa.Column("merged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pr_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Feature-Jira Mapping ───────────────────────────────────────────────
    op.create_table(
        "feature_jira_mapping",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("feature_id", sa.Integer, sa.ForeignKey("features.id"), nullable=False),
        sa.Column("jira_issue_id", sa.Integer, sa.ForeignKey("jira_issues.id"), nullable=False),
        sa.Column("mapping_type", sa.String(50), default="explicit"),
        sa.Column("confidence", sa.Float, default=1.0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Jira-PR Mapping ────────────────────────────────────────────────────
    op.create_table(
        "jira_pr_mapping",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("jira_issue_id", sa.Integer, sa.ForeignKey("jira_issues.id"), nullable=False),
        sa.Column("pull_request_id", sa.Integer, sa.ForeignKey("pull_requests.id"), nullable=False),
        sa.Column("mapping_type", sa.String(50), default="explicit"),
        sa.Column("confidence", sa.Float, default=1.0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Defect Metrics ─────────────────────────────────────────────────────
    op.create_table(
        "defect_metrics",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("feature_id", sa.Integer, sa.ForeignKey("features.id"), nullable=False),
        sa.Column("period", sa.String(50), nullable=False),
        sa.Column("defect_count", sa.Integer, default=0),
        sa.Column("reopen_count", sa.Integer, default=0),
        sa.Column("avg_resolution_hours", sa.Float, nullable=True),
        sa.Column("defect_density", sa.Float, default=0.0),
        sa.Column("severity_distribution", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Workflow Runs ──────────────────────────────────────────────────────
    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("workflow_type", sa.String(100), nullable=False),
        sa.Column("workflow_id", sa.String(255), nullable=False, index=True),
        sa.Column("status", sa.Enum("pending", "running", "completed", "failed", name="workflowstatus"), default="pending"),
        sa.Column("input_params", sa.Text, nullable=True),
        sa.Column("result", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("workflow_runs")
    op.drop_table("defect_metrics")
    op.drop_table("jira_pr_mapping")
    op.drop_table("feature_jira_mapping")
    op.drop_table("pull_requests")
    op.drop_table("jira_issues")
    op.drop_table("features")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS workflowstatus")
    op.execute("DROP TYPE IF EXISTS prstatus")
    op.execute("DROP TYPE IF EXISTS jirastatus")
    op.execute("DROP TYPE IF EXISTS jiraissuetype")
    op.execute("DROP TYPE IF EXISTS userrole")
