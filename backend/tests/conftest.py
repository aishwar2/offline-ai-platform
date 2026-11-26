"""Pytest fixtures configuring an isolated SQLite database and FastAPI TestClient."""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_offline_ai.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-minimum-thirty-two-characters-long")
os.environ.setdefault("RAG_ENABLED", "true")

from app.core.config import get_settings  # noqa: E402
from app.db.session import Base, engine  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    """Recreate schema before each test for deterministic isolation."""
    get_settings.cache_clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient bound to the fresh test database."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def register_and_login(
    client: TestClient,
    email: str = "alice@example.com",
    username: str = "alice",
    password: str = "StrongPass123",
) -> dict[str, str]:
    """Helper to register a user and return Bearer authorization headers."""
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password, "full_name": "Alice"},
    )
    assert reg.status_code == 201, reg.text
    login = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": username, "password": password},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
