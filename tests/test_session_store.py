"""Tests for the session store."""

from app.state_engine.session_store import SessionStore


def test_create_session():
    store = SessionStore()
    session = store.create_session("test_wf", "initial", {"key": "val"})

    assert session.session_id is not None
    assert session.workflow_id == "test_wf"
    assert session.current_state == "initial"
    assert session.context == {"key": "val"}
    assert session.completed is False


def test_get_session():
    store = SessionStore()
    created = store.create_session("wf1", "start")
    fetched = store.get_session(created.session_id)

    assert fetched is not None
    assert fetched.session_id == created.session_id


def test_get_nonexistent_session():
    store = SessionStore()
    assert store.get_session("nonexistent") is None


def test_update_session():
    store = SessionStore()
    session = store.create_session("wf1", "state_a", {"x": 1})

    updated = store.update_session(
        session.session_id,
        new_state="state_b",
        context_updates={"y": 2},
    )

    assert updated is not None
    assert updated.current_state == "state_b"
    assert updated.context["x"] == 1
    assert updated.context["y"] == 2
    assert len(updated.history) == 1
    assert updated.history[0]["from_state"] == "state_a"
    assert updated.history[0]["to_state"] == "state_b"


def test_update_session_completed():
    store = SessionStore()
    session = store.create_session("wf1", "final")
    updated = store.update_session(session.session_id, "end", completed=True)

    assert updated.completed is True


def test_delete_session():
    store = SessionStore()
    session = store.create_session("wf1", "start")
    assert store.delete_session(session.session_id) is True
    assert store.get_session(session.session_id) is None


def test_delete_nonexistent():
    store = SessionStore()
    assert store.delete_session("nope") is False


def test_list_sessions():
    store = SessionStore()
    store.create_session("wf1", "start")
    store.create_session("wf2", "init")

    sessions = store.list_sessions()
    assert len(sessions) == 2
    assert all("session_id" in s for s in sessions)
