"""Live end-to-end checks for the three running microservices."""

import os
from uuid import uuid4

import httpx
from sqlalchemy import create_engine, text


SERVICE_URLS = {
    "user-service": "http://localhost:8000",
    "book-service": "http://localhost:8001",
    "loan-service": "http://localhost:8002",
}

USER_DATABASE_URL = os.getenv(
    "USER_DATABASE_URL",
    "postgresql://testuser:testpass@localhost:5432/user_db",
)


def wait_for_services() -> None:
    for service_name, base_url in SERVICE_URLS.items():
        for _ in range(30):
            try:
                response = httpx.get(f"{base_url}/health", timeout=2.0)
                if response.status_code == 200:
                    break
            except httpx.HTTPError:
                pass
        else:
            raise AssertionError(f"{service_name} did not become healthy")


def test_all_services_are_healthy():
    wait_for_services()


def test_complete_loan_workflow_uses_all_service_http_endpoints():
    wait_for_services()
    email = f"integration-{uuid4().hex}@example.com"
    user_response = httpx.post(
        "http://localhost:8000/api/v1/auth/register",
        json={
            "email": email,
            "password": "integration-password",
            "full_name": "Integration Test",
        },
        timeout=5.0,
    )
    assert user_response.status_code == 201
    user_id = user_response.json()["user"]["id"]

    with create_engine(USER_DATABASE_URL).begin() as connection:
        connection.execute(
            text("UPDATE users SET role = 'LIBRARIAN' WHERE id = :user_id"),
            {"user_id": user_id},
        )

    login_response = httpx.post(
        "http://localhost:8000/api/v1/auth/login",
        json={"email": email, "password": "integration-password"},
        timeout=5.0,
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    authorization = {"Authorization": f"Bearer {access_token}"}

    book_response = httpx.post(
        "http://localhost:8001/api/v1/books/",
        headers=authorization,
        json={
            "title": "Integration Test Book",
            "author": "Integration Author",
            "isbn": f"978{uuid4().int % 10**10:010d}",
            "published_year": 2024,
            "copies_available": 1,
        },
        timeout=5.0,
    )
    assert book_response.status_code == 201
    book_id = book_response.json()["id"]

    loan_response = httpx.post(
        "http://localhost:8002/api/v1/loans/",
        headers=authorization,
        json={
            "user_id": user_id,
            "book_id": book_id,
            "due_date": "2099-01-01T12:00:00",
        },
        timeout=5.0,
    )
    assert loan_response.status_code == 201
    loan_id = loan_response.json()["id"]

    after_loan = httpx.get(f"http://localhost:8001/api/v1/books/{book_id}", timeout=5.0)
    assert after_loan.status_code == 200
    assert after_loan.json()["copies_available"] == 0

    return_response = httpx.post(
        f"http://localhost:8002/api/v1/loans/{loan_id}/return",
        headers=authorization,
        timeout=5.0,
    )
    assert return_response.status_code == 200
    assert return_response.json()["returned"] is True

    after_return = httpx.get(f"http://localhost:8001/api/v1/books/{book_id}", timeout=5.0)
    assert after_return.status_code == 200
    assert after_return.json()["copies_available"] == 1
