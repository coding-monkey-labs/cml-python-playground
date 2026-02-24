"""Pydantic models for the ObjectScale Workbench."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class UIComponent(BaseModel):
    """A single UI component in a state's schema."""

    type: str  # text, select, table, chart, summary, button, message, checkbox
    key: str | None = None
    label: str | None = None
    placeholder: str | None = None
    options: list[dict[str, str]] | None = None
    columns: list[str] | None = None
    data: list[dict[str, Any]] | None = None
    value: Any = None
    required: bool = False
    read_only: bool = False
    variant: str | None = None  # for messages: info, success, warning, danger


class UISchema(BaseModel):
    """The UI schema returned to the frontend for rendering."""

    state_id: str
    title: str
    description: str | None = None
    components: list[UIComponent] = Field(default_factory=list)
    allowed_actions: list[str] = Field(default_factory=list)


class WorkflowStartRequest(BaseModel):
    """Request to start a new workflow."""

    workflow_id: str
    initial_context: dict[str, Any] = Field(default_factory=dict)


class WorkflowStartResponse(BaseModel):
    """Response after starting a workflow."""

    session_id: str
    workflow_id: str
    ui: UISchema


class WorkflowInputRequest(BaseModel):
    """Request to submit user input / transition."""

    session_id: str
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)


class WorkflowStateResponse(BaseModel):
    """Response containing current workflow state."""

    session_id: str
    workflow_id: str
    current_state: str
    ui: UISchema
    context: dict[str, Any] = Field(default_factory=dict)
    completed: bool = False
    error: str | None = None


class ActionResult(BaseModel):
    """Result of executing an action."""

    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
