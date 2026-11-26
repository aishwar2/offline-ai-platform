"""Unit tests for JWT authentication, registration, and user management."""

from fastapi.testclient import TestClient

from tests.conftest import register_and_login


def test_register_login_and_profile(client: TestClient) -> None:
    headers = register_and_login(client)
    me_res = client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    body = me_res.json()
    assert body["username"] == "alice"
    assert body["role"] == "admin"
    assert body["preferred_model"] == "tinyllama"

    patch_res = client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={"preferred_model": "qwen2.5:0.5b", "full_name": "Alice Updated"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["preferred_model"] == "qwen2.5:0.5b"
    assert patch_res.json()["full_name"] == "Alice Updated"


def test_duplicate_registration_and_invalid_login(client: TestClient) -> None:
    register_and_login(client)
    dup = client.post(
        "/api/v1/auth/register",
        json={"email": "alice@example.com", "username": "alice", "password": "StrongPass123"},
    )
    assert dup.status_code == 409

    bad_login = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "alice", "password": "wrong-password"},
    )
    assert bad_login.status_code == 401


def test_admin_rbac_and_user_management(client: TestClient) -> None:
    admin_headers = register_and_login(client, "admin@example.com", "adminuser")
    user_headers = register_and_login(client, "bob@example.com", "bob")

    # Regular user cannot list users
    forbidden = client.get("/api/v1/users", headers=user_headers)
    assert forbidden.status_code == 403

    # Admin lists users and updates Bob
    users_res = client.get("/api/v1/users", headers=admin_headers)
    assert users_res.status_code == 200
    users = users_res.json()
    assert len(users) == 2

    bob_id = next(u["id"] for u in users if u["username"] == "bob")
    update_res = client.patch(
        f"/api/v1/users/{bob_id}",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert update_res.status_code == 200
    assert update_res.json()["is_active"] is False

    del_res = client.delete(f"/api/v1/users/{bob_id}", headers=admin_headers)
    assert del_res.status_code == 204
