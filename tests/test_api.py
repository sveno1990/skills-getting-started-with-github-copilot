import copy
from fastapi.testclient import TestClient
from src.app import app, activities

import pytest

@pytest.fixture(autouse=True)
def client_and_restore():
    # Snapshot state and provide a TestClient, then restore afterwards
    original = copy.deepcopy(activities)
    client = TestClient(app)
    yield client
    activities.clear()
    activities.update(original)


def test_get_activities(client_and_restore):
    client = client_and_restore
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]


def test_signup_and_duplicate_and_delete(client_and_restore):
    client = client_and_restore
    email = "testuser@example.com"
    activity_name = "Chess Club"

    # Ensure clean start
    if email in activities[activity_name]["participants"]:
        activities[activity_name]["participants"].remove(email)

    # Sign up
    resp = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert resp.status_code == 200
    assert f"Signed up {email}" in resp.json().get("message", "")

    # Now participant should be present
    resp = client.get("/activities")
    assert email in resp.json()[activity_name]["participants"]

    # Duplicate signup should fail
    resp = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert resp.status_code == 400

    # Delete participant
    resp = client.delete(f"/activities/{activity_name}/participants?email={email}")
    assert resp.status_code == 200
    assert f"Unregistered {email}" in resp.json().get("message", "")

    # Ensure removed
    resp = client.get("/activities")
    assert email not in resp.json()[activity_name]["participants"]


def test_signup_activity_not_found(client_and_restore):
    client = client_and_restore
    resp = client.post("/activities/NoSuchActivity/signup?email=test@example.com")
    assert resp.status_code == 404


def test_delete_nonexistent_participant(client_and_restore):
    client = client_and_restore
    resp = client.delete("/activities/Chess%20Club/participants?email=nosuch@example.com")
    assert resp.status_code == 404
