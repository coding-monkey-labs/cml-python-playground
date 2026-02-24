"""Tests for the workflow API endpoints."""

import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from app.main import app
from app.api.workflow import init_dependencies
from app.executors.s3_executor import S3Executor
from app.state_engine.engine import StateEngine
from app.state_engine.session_store import SessionStore


@pytest.fixture
def client():
    """Create a test client with mocked S3."""
    with mock_aws():
        executor = S3Executor(
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
            region_name="us-east-1",
        )
        engine = StateEngine(s3_executor=executor)
        store = SessionStore()
        init_dependencies(engine, store)

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_workflows(client):
    response = client.get("/workflow/list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    ids = [w["id"] for w in data]
    assert "list_buckets" in ids


def test_start_workflow(client):
    response = client.post(
        "/workflow/start",
        json={"workflow_id": "create_bucket"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["workflow_id"] == "create_bucket"
    assert "ui" in data
    assert data["ui"]["state_id"] == "input_config"


def test_start_nonexistent_workflow(client):
    response = client.post(
        "/workflow/start",
        json={"workflow_id": "nonexistent"},
    )
    assert response.status_code == 404


def test_get_state(client):
    # Start a workflow
    start_resp = client.post(
        "/workflow/start",
        json={"workflow_id": "create_bucket"},
    )
    session_id = start_resp.json()["session_id"]

    # Get state
    response = client.get(f"/workflow/state/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["current_state"] == "input_config"


def test_get_state_not_found(client):
    response = client.get("/workflow/state/nonexistent")
    assert response.status_code == 404


def test_submit_input_valid(client):
    # Start create_bucket workflow
    start_resp = client.post(
        "/workflow/start",
        json={"workflow_id": "create_bucket"},
    )
    session_id = start_resp.json()["session_id"]

    # Submit input to preview
    response = client.post(
        "/workflow/input",
        json={
            "session_id": session_id,
            "action": "preview",
            "payload": {
                "bucket_name": "test-bucket",
                "region": "us-east-1",
                "versioning": False,
                "object_lock": False,
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_state"] == "preview_config"


def test_submit_input_invalid_action(client):
    start_resp = client.post(
        "/workflow/start",
        json={"workflow_id": "create_bucket"},
    )
    session_id = start_resp.json()["session_id"]

    response = client.post(
        "/workflow/input",
        json={
            "session_id": session_id,
            "action": "invalid_action",
            "payload": {},
        },
    )
    assert response.status_code == 400


def test_submit_input_session_not_found(client):
    response = client.post(
        "/workflow/input",
        json={
            "session_id": "nonexistent",
            "action": "next",
            "payload": {},
        },
    )
    assert response.status_code == 404


def test_full_create_bucket_workflow(client):
    """Test a complete workflow: create_bucket from start to finish."""
    # Start
    start_resp = client.post(
        "/workflow/start",
        json={"workflow_id": "create_bucket"},
    )
    session_id = start_resp.json()["session_id"]

    # Preview
    preview_resp = client.post(
        "/workflow/input",
        json={
            "session_id": session_id,
            "action": "preview",
            "payload": {
                "bucket_name": "workflow-test",
                "region": "us-east-1",
                "versioning": False,
                "object_lock": False,
            },
        },
    )
    assert preview_resp.json()["current_state"] == "preview_config"

    # Confirm -> creating (triggers S3 action)
    confirm_resp = client.post(
        "/workflow/input",
        json={
            "session_id": session_id,
            "action": "confirm",
            "payload": {},
        },
    )
    assert confirm_resp.json()["current_state"] == "creating"

    # Created -> success
    created_resp = client.post(
        "/workflow/input",
        json={
            "session_id": session_id,
            "action": "created",
            "payload": {},
        },
    )
    assert created_resp.json()["current_state"] == "success"

    # Done -> __end__
    done_resp = client.post(
        "/workflow/input",
        json={
            "session_id": session_id,
            "action": "done",
            "payload": {},
        },
    )
    assert done_resp.json()["completed"] is True


def test_versioning_workflow(client):
    """Test the update_versioning workflow."""
    # First create a bucket via executor
    start_resp = client.post(
        "/workflow/start",
        json={"workflow_id": "update_versioning"},
    )
    session_id = start_resp.json()["session_id"]
    assert start_resp.json()["ui"]["state_id"] == "select_bucket"
