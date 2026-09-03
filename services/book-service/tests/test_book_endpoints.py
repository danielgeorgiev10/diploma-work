"""Integration-style tests for Book Service."""

import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.database import Base, engine
from app.dependencies import get_current_user
from app.routes import health as health_routes
import app.routes.book as book_routes
from app.config import Settings, get_settings
from sqlalchemy.exc import SQLAlchemyError


app.dependency_overrides[get_current_user] = lambda: {"id": 1, "role": "librarian"}
book_routes.settings.INTERNAL_SERVICE_TOKEN = "test-internal-token"


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "alive"}


@pytest.mark.asyncio
async def test_unhealthy_readiness_returns_503(monkeypatch):
    def broken_connect():
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(health_routes.engine, "connect", broken_connect)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/ready")
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_create_and_get_book():
    book_payload = {
        "title": "Clean Architecture",
        "author": "Robert C. Martin",
        "isbn": "9780134494166",
        "published_year": 2017,
        "copies_available": 3,
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_response = await client.post("/api/v1/books/", json=book_payload)
        assert create_response.status_code == 201
        created_book = create_response.json()
        assert created_book["title"] == book_payload["title"]
        assert created_book["author"] == book_payload["author"]

        book_id = created_book["id"]
        get_response = await client.get(f"/api/v1/books/{book_id}")
        assert get_response.status_code == 200
        assert get_response.json()["isbn"] == book_payload["isbn"]


@pytest.mark.asyncio
async def test_librarian_can_update_book():
    book_payload = {
        "title": "Before Update",
        "author": "Test Author",
        "isbn": "9780134494170",
        "copies_available": 2,
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post("/api/v1/books/", json=book_payload)
        assert created.status_code == 201

        response = await client.put(
            f"/api/v1/books/{created.json()['id']}",
            json={"title": "After Update", "author": "Updated Author"},
        )

    assert response.status_code == 200
    assert response.json()["title"] == "After Update"
    assert response.json()["author"] == "Updated Author"


@pytest.mark.asyncio
async def test_inventory_decrement_and_increment():
    book_payload = {
        "title": "Inventory Test",
        "author": "Test Author",
        "isbn": "9780134494167",
        "copies_available": 1,
    }
    headers = {"X-Internal-Service-Token": "test-internal-token"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post("/api/v1/books/", json=book_payload)
        book_id = created.json()["id"]
        decremented = await client.patch(
            f"/api/v1/books/{book_id}/inventory/decrement", headers=headers
        )
        assert decremented.status_code == 200
        assert decremented.json()["copies_available"] == 0

        insufficient = await client.patch(
            f"/api/v1/books/{book_id}/inventory/decrement", headers=headers
        )
        assert insufficient.status_code == 409

        incremented = await client.patch(
            f"/api/v1/books/{book_id}/inventory/increment", headers=headers
        )
        assert incremented.status_code == 200
        assert incremented.json()["copies_available"] == 1


@pytest.mark.asyncio
async def test_student_cannot_create_book():
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "role": "student"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/books/",
            json={"title": "Denied", "author": "Author", "isbn": "9780134494168"},
        )
    assert response.status_code == 403
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "role": "librarian"}


@pytest.mark.asyncio
async def test_book_mutation_requires_token():
    app.dependency_overrides.pop(get_current_user, None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/books/",
            json={"title": "Protected", "author": "Author", "isbn": "9780134494169"},
        )
    assert response.status_code == 401
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "role": "librarian"}


def test_production_settings_reject_missing_or_placeholder_token(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("INTERNAL_SERVICE_TOKEN", raising=False)
    get_settings.cache_clear()
    try:
        with pytest.raises(ValueError, match="INTERNAL_SERVICE_TOKEN"):
            get_settings()
    finally:
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("INTERNAL_SERVICE_TOKEN", "test-internal-token")
        get_settings.cache_clear()

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("INTERNAL_SERVICE_TOKEN", "REPLACE_WITH_INTERNAL_SERVICE_TOKEN")
    get_settings.cache_clear()
    try:
        with pytest.raises(ValueError, match="INTERNAL_SERVICE_TOKEN"):
            get_settings()
    finally:
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("INTERNAL_SERVICE_TOKEN", "test-internal-token")
        get_settings.cache_clear()


def test_valid_explicit_internal_token_is_accepted():
    book_routes.settings.INTERNAL_SERVICE_TOKEN = "test-internal-token"
    book_routes.validate_internal_token("test-internal-token")
