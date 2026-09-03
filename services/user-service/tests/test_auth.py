"""Authentication tests."""

import pytest
from datetime import timedelta
from datetime import datetime, timezone
import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.schemas import UserRegister
from app.utils.security import create_access_token, create_refresh_token
from app.utils import security
from app.routes import users as users_routes

users_routes.settings.INTERNAL_SERVICE_TOKEN = "test-internal-token"


# Use in-memory SQLite for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup and teardown for each test."""
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if previous_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous_override


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readiness_check_healthy():
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readiness_check_unhealthy():
    class BrokenSession:
        def execute(self, statement):
            raise RuntimeError("database unavailable")

        def close(self):
            pass

    def broken_db():
        yield BrokenSession()

    app.dependency_overrides[get_db] = broken_db
    try:
        response = client.get("/health/ready")
    finally:
        app.dependency_overrides[get_db] = override_get_db

    assert response.status_code == 503


def test_user_registration():
    """Test user registration."""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    assert response.json()["message"] == "User registered successfully"
    assert response.json()["user"]["email"] == "test@example.com"


def test_user_registration_duplicate_email():
    """Test duplicate email registration fails."""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    # Try to register again with same email
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 409


def test_user_login():
    """Test user login."""
    # Register user first
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    # Login
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123",
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_user_login_invalid_password():
    """Test login with invalid password fails."""
    # Register user first
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    # Try to login with wrong password
    login_data = {
        "email": "test@example.com",
        "password": "wrongpassword",
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401


def test_current_user_requires_token():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_current_user_accepts_valid_access_token():
    user_data = {
        "email": "valid@example.com",
        "password": "testpassword123",
        "full_name": "Valid User",
    }
    registration = client.post("/api/v1/auth/register", json=user_data)
    user_id = registration.json()["user"]["id"]
    token = create_access_token({"sub": str(user_id), "email": user_data["email"]})

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == user_id


def test_current_user_rejects_invalid_token():
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_current_user_rejects_expired_token():
    token = create_access_token({"sub": "1"}, expires_delta=timedelta(seconds=-1))
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_current_user_rejects_refresh_token():
    token = create_refresh_token({"sub": "1"})
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_current_user_rejects_token_without_type():
    token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        security.settings.SECRET_KEY,
        algorithm=security.settings.ALGORITHM,
    )
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_user_lookup_requires_internal_service_token():
    user_data = {
        "email": "lookup@example.com",
        "password": "testpassword123",
        "full_name": "Lookup User",
    }
    registration = client.post("/api/v1/auth/register", json=user_data)
    user_id = registration.json()["user"]["id"]

    unauthorized = client.get(f"/api/v1/users/{user_id}")
    assert unauthorized.status_code == 401

    authorized = client.get(
        f"/api/v1/users/{user_id}",
        headers={"X-Internal-Service-Token": "test-internal-token"},
    )
    assert authorized.status_code == 200
    assert authorized.json()["id"] == user_id
