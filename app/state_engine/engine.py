"""Core state machine engine for workflow execution."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from app.executors.s3_executor import S3Executor
from app.models import ActionResult, UIComponent, UISchema

logger = logging.getLogger(__name__)

WORKFLOWS_DIR = Path(__file__).parent.parent / "workflows"


class WorkflowNotFoundError(Exception):
    pass


class InvalidTransitionError(Exception):
    pass


class StateEngine:
    """Loads YAML workflows, validates transitions, and drives execution."""

    def __init__(self, s3_executor: S3Executor | None = None):
        self._workflows: dict[str, dict[str, Any]] = {}
        self._s3_executor = s3_executor or S3Executor()
        self._load_workflows()

    def _load_workflows(self) -> None:
        """Load all YAML workflow definitions from the workflows directory."""
        if not WORKFLOWS_DIR.exists():
            logger.warning("Workflows directory not found: %s", WORKFLOWS_DIR)
            return
        for path in WORKFLOWS_DIR.glob("*.yaml"):
            try:
                with open(path) as f:
                    workflow = yaml.safe_load(f)
                if workflow and "id" in workflow:
                    self._workflows[workflow["id"]] = workflow
                    logger.info("Loaded workflow: %s", workflow["id"])
            except Exception:
                logger.exception("Failed to load workflow: %s", path)

    def reload_workflows(self) -> None:
        """Reload all workflow definitions."""
        self._workflows.clear()
        self._load_workflows()

    def list_workflows(self) -> list[dict[str, str]]:
        """Return a summary of all available workflows."""
        return [
            {
                "id": wf["id"],
                "name": wf.get("name", wf["id"]),
                "description": wf.get("description", ""),
            }
            for wf in self._workflows.values()
        ]

    def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        """Get a workflow definition by ID."""
        if workflow_id not in self._workflows:
            raise WorkflowNotFoundError(f"Workflow not found: {workflow_id}")
        return self._workflows[workflow_id]

    def get_initial_state(self, workflow_id: str) -> str:
        """Return the initial state name for a workflow."""
        wf = self.get_workflow(workflow_id)
        return wf["initial_state"]

    def get_state_def(self, workflow_id: str, state_name: str) -> dict[str, Any]:
        """Get the state definition from a workflow."""
        wf = self.get_workflow(workflow_id)
        states = wf.get("states", {})
        if state_name not in states:
            raise InvalidTransitionError(
                f"State '{state_name}' not found in workflow '{workflow_id}'"
            )
        return states[state_name]

    def get_allowed_transitions(self, workflow_id: str, state_name: str) -> list[str]:
        """Get allowed transition names from a state."""
        state_def = self.get_state_def(workflow_id, state_name)
        transitions = state_def.get("transitions", [])
        return [t["action"] for t in transitions] if isinstance(transitions, list) else []

    def validate_transition(
        self, workflow_id: str, current_state: str, action: str
    ) -> dict[str, Any] | None:
        """Validate and return the transition definition, or None if invalid."""
        state_def = self.get_state_def(workflow_id, current_state)
        transitions = state_def.get("transitions", [])
        for t in transitions:
            if t["action"] == action:
                return t
        return None

    def build_ui_schema(
        self, workflow_id: str, state_name: str, context: dict[str, Any]
    ) -> UISchema:
        """Build the UI schema for a given state, interpolating context values."""
        state_def = self.get_state_def(workflow_id, state_name)
        ui_def = state_def.get("ui", {})

        title = self._interpolate(ui_def.get("title", state_name), context)
        description = self._interpolate(ui_def.get("description", ""), context)

        components = []
        for comp_def in ui_def.get("components", []):
            comp = UIComponent(
                type=comp_def.get("type", "text"),
                key=comp_def.get("key"),
                label=self._interpolate(comp_def.get("label", ""), context),
                placeholder=comp_def.get("placeholder"),
                options=comp_def.get("options"),
                columns=comp_def.get("columns"),
                data=context.get(comp_def["key"]) if comp_def.get("data_from_context") else comp_def.get("data"),
                value=context.get(comp_def["key"]) if comp_def.get("value_from_context") and comp_def.get("key") else comp_def.get("value"),
                required=comp_def.get("required", False),
                read_only=comp_def.get("read_only", False),
                variant=comp_def.get("variant"),
            )
            components.append(comp)

        allowed_actions = self.get_allowed_transitions(workflow_id, state_name)

        return UISchema(
            state_id=state_name,
            title=title,
            description=description,
            components=components,
            allowed_actions=allowed_actions,
        )

    def execute_action(
        self, workflow_id: str, state_name: str, context: dict[str, Any]
    ) -> ActionResult:
        """Execute the action defined in a state (if any)."""
        state_def = self.get_state_def(workflow_id, state_name)
        action_def = state_def.get("action")

        if not action_def:
            return ActionResult(success=True, data={})

        action_type = action_def.get("type", "")
        operation = action_def.get("operation", "")
        params = self._resolve_params(action_def.get("params", {}), context)

        try:
            if action_type == "s3_call":
                result = self._s3_executor.execute(operation, params)
                return ActionResult(success=True, data=result)
            elif action_type == "bulk_s3_call":
                items = context.get(action_def.get("items_key", "items"), [])
                results = self._s3_executor.execute_bulk(operation, params, items)
                return ActionResult(success=True, data={"results": results})
            elif action_type == "validation":
                return ActionResult(success=True, data={})
            elif action_type == "computed_summary":
                return ActionResult(success=True, data=context)
            else:
                return ActionResult(success=False, error=f"Unknown action type: {action_type}")
        except Exception as e:
            logger.exception("Action execution failed")
            return ActionResult(success=False, error=str(e))

    def _resolve_params(
        self, params: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve parameter values from context references."""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$ctx."):
                ctx_key = value[5:]  # strip "$ctx."
                resolved[key] = context.get(ctx_key, value)
            else:
                resolved[key] = value
        return resolved

    def _interpolate(self, text: str, context: dict[str, Any]) -> str:
        """Interpolate {{key}} placeholders with context values."""
        if not text:
            return text
        result = text
        for key, value in context.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result
