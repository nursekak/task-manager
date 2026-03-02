import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    """Register, then return Authorization header."""
    client.post(
        "/v1/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    resp = client.post(
        "/v1/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


def test_register_ok(client: TestClient) -> None:
    resp = client.post(
        "/v1/auth/register",
        json={"email": "new@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert "id" in data
    assert "created_at" in data


def test_register_duplicate_email(client: TestClient) -> None:
    client.post(
        "/v1/auth/register",
        json={"email": "dup@example.com", "password": "password123"},
    )
    resp = client.post(
        "/v1/auth/register",
        json={"email": "dup@example.com", "password": "other"},
    )
    assert resp.status_code == 400


def test_login_ok(client: TestClient) -> None:
    client.post(
        "/v1/auth/register",
        json={"email": "login@example.com", "password": "secret456"},
    )
    resp = client.post(
        "/v1/auth/login",
        json={"email": "login@example.com", "password": "secret456"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.json()["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient) -> None:
    client.post(
        "/v1/auth/register",
        json={"email": "wrong@example.com", "password": "good"},
    )
    resp = client.post(
        "/v1/auth/login",
        json={"email": "wrong@example.com", "password": "bad"},
    )
    assert resp.status_code == 401
