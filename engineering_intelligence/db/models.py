"""SQLAlchemy ORM models for the relational database layer."""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from engineering_intelligence.db.base import Base


# ── Enums ──────────────────────────────────────────────────────────────────────


class UserRole(str, enum.Enum):
    DEVELOPER = "developer"
    ADMIN = "admin"


class JiraIssueType(str, enum.Enum):
    EPIC = "epic"
    STORY = "story"
    TASK = "task"
    DEFECT = "defect"
    SUB_TASK = "sub_task"


class JiraStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class PRStatus(str, enum.Enum):
    OPEN = "open"
    MERGED = "merged"
    CLOSED = "closed"


class WorkflowStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ── Mixins ─────────────────────────────────────────────────────────────────────


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ── User & Role ────────────────────────────────────────────────────────────────


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.DEVELOPER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# ── Feature ────────────────────────────────────────────────────────────────────


class Feature(TimestampMixin, Base):
    __tablename__ = "features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("features.id"), nullable=True
    )
    defect_count: Mapped[int] = mapped_column(Integer, default=0)
    health_score: Mapped[float] = mapped_column(Float, default=100.0)

    parent: Mapped["Feature | None"] = relationship(
        "Feature", remote_side="Feature.id", back_populates="children"
    )
    children: Mapped[list["Feature"]] = relationship("Feature", back_populates="parent")
    jira_mappings: Mapped[list["FeatureJiraMapping"]] = relationship(back_populates="feature")


# ── Jira Issue ─────────────────────────────────────────────────────────────────


class JiraIssue(TimestampMixin, Base):
    __tablename__ = "jira_issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    jira_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    issue_type: Mapped[JiraIssueType] = mapped_column(Enum(JiraIssueType), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[JiraStatus] = mapped_column(Enum(JiraStatus), default=JiraStatus.OPEN)
    priority: Mapped[str | None] = mapped_column(String(50), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    assignee_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reporter_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parent_key: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    epic_key: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    resolution: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reopen_count: Mapped[int] = mapped_column(Integer, default=0)
    resolution_time_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    labels: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array stored as text
    components: Mapped[str | None] = mapped_column(Text, nullable=True)
    jira_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    jira_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    feature_mappings: Mapped[list["FeatureJiraMapping"]] = relationship(back_populates="jira_issue")
    pr_mappings: Mapped[list["JiraPRMapping"]] = relationship(back_populates="jira_issue")


# ── Pull Request ───────────────────────────────────────────────────────────────


class PullRequest(TimestampMixin, Base):
    __tablename__ = "pull_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    repo: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PRStatus] = mapped_column(Enum(PRStatus), default=PRStatus.OPEN)
    author_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_login: Mapped[str | None] = mapped_column(String(255), nullable=True)
    files_changed: Mapped[int] = mapped_column(Integer, default=0)
    additions: Mapped[int] = mapped_column(Integer, default=0)
    deletions: Mapped[int] = mapped_column(Integer, default=0)
    merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pr_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    jira_mappings: Mapped[list["JiraPRMapping"]] = relationship(back_populates="pull_request")


# ── Mapping Tables ─────────────────────────────────────────────────────────────


class FeatureJiraMapping(TimestampMixin, Base):
    __tablename__ = "feature_jira_mapping"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feature_id: Mapped[int] = mapped_column(Integer, ForeignKey("features.id"), nullable=False)
    jira_issue_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jira_issues.id"), nullable=False
    )
    mapping_type: Mapped[str] = mapped_column(
        String(50), default="explicit"
    )  # explicit | inferred
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    feature: Mapped[Feature] = relationship(back_populates="jira_mappings")
    jira_issue: Mapped[JiraIssue] = relationship(back_populates="feature_mappings")


class JiraPRMapping(TimestampMixin, Base):
    __tablename__ = "jira_pr_mapping"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    jira_issue_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jira_issues.id"), nullable=False
    )
    pull_request_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pull_requests.id"), nullable=False
    )
    mapping_type: Mapped[str] = mapped_column(String(50), default="explicit")
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    jira_issue: Mapped[JiraIssue] = relationship(back_populates="pr_mappings")
    pull_request: Mapped[PullRequest] = relationship(back_populates="jira_mappings")


# ── Defect Metrics ─────────────────────────────────────────────────────────────


class DefectMetrics(TimestampMixin, Base):
    __tablename__ = "defect_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feature_id: Mapped[int] = mapped_column(Integer, ForeignKey("features.id"), nullable=False)
    period: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "2024-Q1"
    defect_count: Mapped[int] = mapped_column(Integer, default=0)
    reopen_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_resolution_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    defect_density: Mapped[float] = mapped_column(Float, default=0.0)
    severity_distribution: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON


# ── Workflow Runs ──────────────────────────────────────────────────────────────


class WorkflowRun(TimestampMixin, Base):
    __tablename__ = "workflow_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_type: Mapped[str] = mapped_column(String(100), nullable=False)
    workflow_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus), default=WorkflowStatus.PENDING
    )
    input_params: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    result: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
