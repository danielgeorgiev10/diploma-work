from datetime import timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import User, UserRole
from app.services import user_service as user_service_module
from app.utils.security import create_access_token, hash_password
from app.routes import users as users_routes


engine = create_engine("sqlite:///./user-management-test.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

users_routes.settings.INTERNAL_SERVICE_TOKEN = "test-internal-token"
client = TestClient(app)


@pytest.fixture(autouse=True)
def database():
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    admin = User(email="admin@example.com", password_hash=hash_password("password"), full_name="Main Admin", role=UserRole.ADMIN)
    librarian = User(email="librarian@example.com", password_hash=hash_password("password"), full_name="Library Staff", role=UserRole.LIBRARIAN)
    student = User(email="student@example.com", password_hash=hash_password("password"), full_name="Student User", role=UserRole.STUDENT)
    db.add_all([admin, librarian, student])
    db.commit()
    db.refresh(admin)
    db.refresh(librarian)
    db.refresh(student)
    yield {"admin": admin, "librarian": librarian, "student": student}
    db.close()
    Base.metadata.drop_all(bind=engine)
    if previous_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous_override


def auth_header(user):
    token = create_access_token({"sub": str(user.id), "email": user.email}, timedelta(minutes=5))
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_list_and_search_users(database):
    response = client.get("/api/v1/users/", headers=auth_header(database["admin"]))
    assert response.status_code == 200
    assert {user["email"] for user in response.json()} == {
        "admin@example.com", "librarian@example.com", "student@example.com"
    }
    search = client.get("/api/v1/users/?search=Library", headers=auth_header(database["admin"]))
    assert search.status_code == 200
    assert [user["email"] for user in search.json()] == ["librarian@example.com"]
    assert all("password_hash" not in user for user in response.json())


def test_only_admin_can_manage_users(database):
    for user_key in ("librarian", "student"):
        response = client.get("/api/v1/users/", headers=auth_header(database[user_key]))
        assert response.status_code == 403
        response = client.patch(
            f"/api/v1/users/{database['student'].id}/status",
            json={"is_active": False},
            headers=auth_header(database[user_key]),
        )
        assert response.status_code == 403
    assert client.get("/api/v1/users/").status_code == 401


def test_admin_can_change_role_and_status(database):
    admin_headers = auth_header(database["admin"])
    role_response = client.patch(
        f"/api/v1/users/{database['student'].id}/role",
        json={"role": "librarian"},
        headers=admin_headers,
    )
    assert role_response.status_code == 200
    assert role_response.json()["role"] == "librarian"

    status_response = client.patch(
        f"/api/v1/users/{database['student'].id}/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert status_response.status_code == 200
    assert status_response.json()["is_active"] is False
    status_response = client.patch(
        f"/api/v1/users/{database['student'].id}/status",
        json={"is_active": True},
        headers=admin_headers,
    )
    assert status_response.status_code == 200
    assert status_response.json()["is_active"] is True


def test_last_admin_protection(database):
    response = client.patch(
        f"/api/v1/users/{database['admin'].id}/role",
        json={"role": "student"},
        headers=auth_header(database["admin"]),
    )
    assert response.status_code == 409
    response = client.patch(
        f"/api/v1/users/{database['admin'].id}/status",
        json={"is_active": False},
        headers=auth_header(database["admin"]),
    )
    assert response.status_code == 409


def test_delete_requires_no_loan_history(database, monkeypatch):
    monkeypatch.setattr(
        user_service_module.httpx,
        "get",
        lambda *args, **kwargs: SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"has_loans": True}),
    )
    response = client.delete(
        f"/api/v1/users/{database['student'].id}",
        headers=auth_header(database["admin"]),
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Cannot delete a user with loan history."

    monkeypatch.setattr(
        user_service_module.httpx,
        "get",
        lambda *args, **kwargs: SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"has_loans": False}),
    )
    response = client.delete(
        f"/api/v1/users/{database['student'].id}",
        headers=auth_header(database["admin"]),
    )
    assert response.status_code == 204


def test_internal_lookup_still_requires_service_token(database):
    response = client.get(f"/api/v1/users/{database['student'].id}")
    assert response.status_code == 401
    response = client.get(
        f"/api/v1/users/{database['student'].id}",
        headers={"X-Internal-Service-Token": "test-internal-token"},
    )
    assert response.status_code == 200
    assert "password_hash" not in response.json()
