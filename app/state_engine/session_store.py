"""In-memory session store for workflow state management."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Session:
    """A workflow execution session."""

    session_id: str
    workflow_id: str
    current_state: str
    context: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    completed: bool = False
    error: str | None = None


class SessionStore:
    """In-memory session store. Replace with Redis/DB for production."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create_session(
        self,
        workflow_id: str,
        initial_state: str,
        initial_context: dict[str, Any] | None = None,
    ) -> Session:
        """Create a new workflow session."""
        session_id = str(uuid.uuid4())
        session = Session(
            session_id=session_id,
            workflow_id=workflow_id,
            current_state=initial_state,
            context=initial_context or {},
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Session | None:
        """Retrieve a session by ID."""
        return self._sessions.get(session_id)

    def update_session(
        self,
        session_id: str,
        new_state: str,
        context_updates: dict[str, Any] | None = None,
        completed: bool = False,
        error: str | None = None,
    ) -> Session | None:
        """Update session state and context."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        # Record history
        session.history.append(
            {
                "from_state": session.current_state,
                "to_state": new_state,
                "context_snapshot": dict(session.context),
            }
        )

        session.current_state = new_state
        if context_updates:
            session.context.update(context_updates)
        session.completed = completed
        session.error = error
        return session

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all active sessions."""
        return [
            {
                "session_id": s.session_id,
                "workflow_id": s.workflow_id,
                "current_state": s.current_state,
                "completed": s.completed,
            }
            for s in self._sessions.values()
        ]
