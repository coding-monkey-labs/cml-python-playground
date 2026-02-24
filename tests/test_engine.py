"""Tests for the state engine."""

import pytest

from app.state_engine.engine import (
    InvalidTransitionError,
    StateEngine,
    WorkflowNotFoundError,
)


@pytest.fixture
def engine():
    """Create an engine with test credentials (no real S3)."""
    return StateEngine()


def test_load_workflows(engine):
    workflows = engine.list_workflows()
    assert len(workflows) > 0
    ids = [w["id"] for w in workflows]
    assert "list_buckets" in ids
    assert "create_bucket" in ids
    assert "inspect_bucket" in ids


def test_get_workflow(engine):
    wf = engine.get_workflow("list_buckets")
    assert wf["id"] == "list_buckets"
    assert "states" in wf
    assert "initial_state" in wf


def test_get_workflow_not_found(engine):
    with pytest.raises(WorkflowNotFoundError):
        engine.get_workflow("nonexistent")


def test_get_initial_state(engine):
    state = engine.get_initial_state("create_bucket")
    assert state == "input_config"


def test_get_state_def(engine):
    state_def = engine.get_state_def("create_bucket", "input_config")
    assert "ui" in state_def
    assert "transitions" in state_def


def test_get_state_def_invalid(engine):
    with pytest.raises(InvalidTransitionError):
        engine.get_state_def("create_bucket", "nonexistent_state")


def test_get_allowed_transitions(engine):
    transitions = engine.get_allowed_transitions("create_bucket", "input_config")
    assert "preview" in transitions


def test_validate_transition_valid(engine):
    transition = engine.validate_transition("create_bucket", "input_config", "preview")
    assert transition is not None
    assert transition["target"] == "preview_config"


def test_validate_transition_invalid(engine):
    transition = engine.validate_transition("create_bucket", "input_config", "invalid")
    assert transition is None


def test_build_ui_schema(engine):
    ui = engine.build_ui_schema("create_bucket", "input_config", {})
    assert ui.state_id == "input_config"
    assert ui.title == "Create New Bucket"
    assert len(ui.components) > 0
    assert "preview" in ui.allowed_actions


def test_build_ui_schema_interpolation(engine):
    ctx = {"bucket_name": "my-test-bucket"}
    ui = engine.build_ui_schema("create_bucket", "preview_config", ctx)
    assert "my-test-bucket" in ui.title or any(
        "my-test-bucket" in (c.label or "") for c in ui.components
    )


def test_interpolate(engine):
    result = engine._interpolate("Hello {{name}}, bucket {{bucket}}", {"name": "World", "bucket": "b1"})
    assert result == "Hello World, bucket b1"


def test_interpolate_empty(engine):
    assert engine._interpolate("", {}) == ""
    assert engine._interpolate("no placeholders", {}) == "no placeholders"


def test_resolve_params(engine):
    params = {"bucket_name": "$ctx.name", "static": "value"}
    ctx = {"name": "test-bucket"}
    resolved = engine._resolve_params(params, ctx)
    assert resolved["bucket_name"] == "test-bucket"
    assert resolved["static"] == "value"


def test_all_workflows_have_required_fields(engine):
    """Every workflow must have id, initial_state, and states."""
    for wf_summary in engine.list_workflows():
        wf = engine.get_workflow(wf_summary["id"])
        assert "id" in wf
        assert "initial_state" in wf
        assert "states" in wf
        assert wf["initial_state"] in wf["states"]


def test_all_transitions_target_valid_states(engine):
    """Every transition target must be a valid state or __end__."""
    for wf_summary in engine.list_workflows():
        wf = engine.get_workflow(wf_summary["id"])
        states = wf["states"]
        for state_name, state_def in states.items():
            for t in state_def.get("transitions", []):
                target = t["target"]
                assert target == "__end__" or target in states, (
                    f"Invalid target '{target}' in {wf_summary['id']}.{state_name}"
                )
