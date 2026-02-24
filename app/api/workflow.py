"""Workflow API routes for the ObjectScale Workbench."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models import (
    WorkflowInputRequest,
    WorkflowStartRequest,
    WorkflowStartResponse,
    WorkflowStateResponse,
)
from app.state_engine.engine import (
    InvalidTransitionError,
    StateEngine,
    WorkflowNotFoundError,
)
from app.state_engine.session_store import SessionStore

router = APIRouter(prefix="/workflow", tags=["workflow"])

# Shared instances (injected from main.py via app.state)
_engine: StateEngine | None = None
_session_store: SessionStore | None = None


def init_dependencies(engine: StateEngine, session_store: SessionStore) -> None:
    """Initialize module-level dependencies. Called from main.py."""
    global _engine, _session_store
    _engine = engine
    _session_store = session_store


def _get_engine() -> StateEngine:
    if _engine is None:
        raise RuntimeError("State engine not initialized")
    return _engine


def _get_store() -> SessionStore:
    if _session_store is None:
        raise RuntimeError("Session store not initialized")
    return _session_store


@router.get("/list")
def list_workflows() -> list[dict[str, str]]:
    """List all available workflows."""
    return _get_engine().list_workflows()


@router.post("/start", response_model=WorkflowStartResponse)
def start_workflow(req: WorkflowStartRequest) -> WorkflowStartResponse:
    """Start a new workflow session."""
    engine = _get_engine()
    store = _get_store()

    try:
        initial_state = engine.get_initial_state(req.workflow_id)
    except WorkflowNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    session = store.create_session(
        workflow_id=req.workflow_id,
        initial_state=initial_state,
        initial_context=req.initial_context,
    )

    # Check if initial state has an action to execute
    action_result = engine.execute_action(
        req.workflow_id, initial_state, session.context
    )
    if action_result.success and action_result.data:
        session.context.update(action_result.data)

    ui = engine.build_ui_schema(req.workflow_id, initial_state, session.context)

    return WorkflowStartResponse(
        session_id=session.session_id,
        workflow_id=req.workflow_id,
        ui=ui,
    )


@router.post("/input", response_model=WorkflowStateResponse)
def submit_input(req: WorkflowInputRequest) -> WorkflowStateResponse:
    """Submit user input and advance workflow state."""
    engine = _get_engine()
    store = _get_store()

    session = store.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.completed:
        raise HTTPException(status_code=400, detail="Workflow already completed")

    # Validate transition
    transition = engine.validate_transition(
        session.workflow_id, session.current_state, req.action
    )
    if not transition:
        allowed = engine.get_allowed_transitions(
            session.workflow_id, session.current_state
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action '{req.action}'. Allowed: {allowed}",
        )

    # Update context with user payload
    context_updates = dict(req.payload)

    # Determine next state
    next_state = transition["target"]
    is_completed = next_state == "__end__"

    # Merge context
    merged_context = {**session.context, **context_updates}

    # Execute action if defined in the target state
    if not is_completed:
        try:
            action_result = engine.execute_action(
                session.workflow_id, next_state, merged_context
            )
            if action_result.success and action_result.data:
                merged_context.update(action_result.data)
            elif not action_result.success:
                # Store error but still transition
                merged_context["_last_error"] = action_result.error
        except Exception as e:
            merged_context["_last_error"] = str(e)

    # Update session
    store.update_session(
        session_id=req.session_id,
        new_state=next_state,
        context_updates=merged_context,
        completed=is_completed,
    )

    # Build UI for new state
    if is_completed:
        from app.models import UISchema

        ui = UISchema(
            state_id="__end__",
            title="Workflow Complete",
            components=[],
            allowed_actions=[],
        )
    else:
        ui = engine.build_ui_schema(
            session.workflow_id, next_state, merged_context
        )

    # Get updated session
    updated_session = store.get_session(req.session_id)

    return WorkflowStateResponse(
        session_id=req.session_id,
        workflow_id=session.workflow_id,
        current_state=next_state,
        ui=ui,
        context=merged_context,
        completed=is_completed,
    )


@router.get("/state/{session_id}", response_model=WorkflowStateResponse)
def get_state(session_id: str) -> WorkflowStateResponse:
    """Get the current state of a workflow session."""
    engine = _get_engine()
    store = _get_store()

    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.completed:
        from app.models import UISchema

        ui = UISchema(
            state_id="__end__",
            title="Workflow Complete",
            components=[],
            allowed_actions=[],
        )
    else:
        ui = engine.build_ui_schema(
            session.workflow_id, session.current_state, session.context
        )

    return WorkflowStateResponse(
        session_id=session.session_id,
        workflow_id=session.workflow_id,
        current_state=session.current_state,
        ui=ui,
        context=session.context,
        completed=session.completed,
        error=session.error,
    )
