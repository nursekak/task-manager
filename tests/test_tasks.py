import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/v1/auth/register",
        json={"email": "taskuser@example.com", "password": "password123"},
    )
    resp = client.post(
        "/v1/auth/login",
        json={"email": "taskuser@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_create_task(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.post(
        "/v1/tasks/",
        json={
            "title": "My task",
            "description": "Do something",
            "status": "pending",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "My task"
    assert data["description"] == "Do something"
    assert data["status"] == "pending"
    assert "id" in data
    assert data["user_id"]  # set by backend


def test_list_tasks(client: TestClient, auth_headers: dict[str, str]) -> None:
    client.post(
        "/v1/tasks/",
        json={"title": "T1", "status": "pending"},
        headers=auth_headers,
    )
    client.post(
        "/v1/tasks/",
        json={"title": "T2", "status": "done"},
        headers=auth_headers,
    )
    resp = client.get("/v1/tasks/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2
    assert data["page"] == 1
    assert "pages" in data


def test_list_tasks_filter_by_status(client: TestClient, auth_headers: dict[str, str]) -> None:
    client.post("/v1/tasks/", json={"title": "P", "status": "pending"}, headers=auth_headers)
    client.post("/v1/tasks/", json={"title": "D", "status": "done"}, headers=auth_headers)
    resp = client.get("/v1/tasks/?status=done", headers=auth_headers)
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["status"] == "done"


def test_get_task(client: TestClient, auth_headers: dict[str, str]) -> None:
    create = client.post(
        "/v1/tasks/",
        json={"title": "Get me", "status": "pending"},
        headers=auth_headers,
    )
    task_id = create.json()["id"]
    resp = client.get(f"/v1/tasks/{task_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Get me"


def test_get_task_404(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.get("/v1/tasks/99999", headers=auth_headers)
    assert resp.status_code == 404


def test_update_task(client: TestClient, auth_headers: dict[str, str]) -> None:
    create = client.post(
        "/v1/tasks/",
        json={"title": "Original", "status": "pending"},
        headers=auth_headers,
    )
    task_id = create.json()["id"]
    resp = client.patch(
        f"/v1/tasks/{task_id}",
        json={"title": "Updated", "status": "in_progress"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"
    assert resp.json()["status"] == "in_progress"


def test_delete_task(client: TestClient, auth_headers: dict[str, str]) -> None:
    create = client.post(
        "/v1/tasks/",
        json={"title": "To delete", "status": "pending"},
        headers=auth_headers,
    )
    task_id = create.json()["id"]
    resp = client.delete(f"/v1/tasks/{task_id}", headers=auth_headers)
    assert resp.status_code == 204
    get_resp = client.get(f"/v1/tasks/{task_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_tasks_require_auth(client: TestClient) -> None:
    resp = client.get("/v1/tasks/")
    assert resp.status_code == 401


def test_root(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Task Manager API"
