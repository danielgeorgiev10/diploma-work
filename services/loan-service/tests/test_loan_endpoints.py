"""Integration-style tests for Loan Service."""

from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.database import Base, engine
from app.dependencies import get_current_user
from app.utils.service_clients import ServiceClient, ServiceClientError
from app.routes import health as health_routes
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from app.schemas.loan import LoanCreate
from app.services.loan_service import LoanService
from app.models.loan import Loan


app.dependency_overrides[get_current_user] = lambda: {"id": 1, "role": "student"}


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
async def test_create_and_return_loan(monkeypatch):
    inventory = {"copies_available": 1}
    calls = []

    monkeypatch.setattr(ServiceClient, "get_user", staticmethod(lambda user_id: {"id": user_id}))
    monkeypatch.setattr(ServiceClient, "get_book", staticmethod(lambda book_id: dict(inventory)))

    def update_inventory(book_id, delta):
        inventory["copies_available"] += delta
        calls.append(delta)
        if inventory["copies_available"] < 0:
            raise ValueError("Not enough copies available")
        return dict(inventory)

    monkeypatch.setattr(ServiceClient, "update_book_inventory", staticmethod(update_inventory))
    payload = {
        "user_id": 1,
        "book_id": 1,
        "due_date": (datetime.utcnow() + timedelta(days=14)).isoformat(),
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_response = await client.post("/api/v1/loans/", json=payload)
        assert create_response.status_code == 201
        loan_data = create_response.json()
        assert loan_data["user_id"] == payload["user_id"]
        assert loan_data["book_id"] == payload["book_id"]
        assert loan_data["returned"] is False

        loan_id = loan_data["id"]
        return_response = await client.post(f"/api/v1/loans/{loan_id}/return")
        assert return_response.status_code == 200
        assert return_response.json()["returned"] is True
        assert inventory["copies_available"] == 1
        assert calls == [-1, 1]

        repeated_return = await client.post(f"/api/v1/loans/{loan_id}/return")
        assert repeated_return.status_code == 200
        assert calls == [-1, 1]


@pytest.mark.asyncio
async def test_downstream_book_service_failure_returns_503(monkeypatch):
    monkeypatch.setattr(ServiceClient, "get_user", staticmethod(lambda user_id: {"id": user_id}))
    monkeypatch.setattr(
        ServiceClient,
        "get_book",
        staticmethod(lambda book_id: {"id": book_id, "copies_available": 1}),
    )
    monkeypatch.setattr(
        ServiceClient,
        "update_book_inventory",
        staticmethod(lambda book_id, delta: (_ for _ in ()).throw(ServiceClientError("Book service unavailable", 503))),
    )

    payload = {
        "user_id": 1,
        "book_id": 1,
        "due_date": (datetime.utcnow() + timedelta(days=14)).isoformat(),
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/loans/", json=payload)
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_loan_creation_requires_token():
    app.dependency_overrides.pop(get_current_user, None)
    payload = {
        "user_id": 1,
        "book_id": 1,
        "due_date": (datetime.utcnow() + timedelta(days=14)).isoformat(),
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/loans/", json=payload)
    assert response.status_code == 401
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "role": "student"}


def test_loan_commit_failure_compensates_inventory(monkeypatch):
    calls = []

    monkeypatch.setattr(ServiceClient, "get_user", staticmethod(lambda user_id: {"id": user_id}))
    monkeypatch.setattr(
        ServiceClient,
        "get_book",
        staticmethod(lambda book_id: {"id": book_id, "copies_available": 1}),
    )
    monkeypatch.setattr(
        ServiceClient,
        "update_book_inventory",
        staticmethod(lambda book_id, delta: calls.append(delta) or {"copies_available": 1 + delta}),
    )

    class FailingDatabase:
        def add(self, loan):
            pass

        def commit(self):
            raise SQLAlchemyError("database write failed")

        def rollback(self):
            pass

    loan_data = LoanCreate(
        user_id=1,
        book_id=1,
        due_date=datetime.utcnow() + timedelta(days=14),
    )

    with pytest.raises(RuntimeError):
        LoanService.create_loan(FailingDatabase(), loan_data)

    assert calls == [-1, 1]


def test_concurrent_returns_increment_inventory_once(monkeypatch):
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    seed_session = session_factory()
    loan = Loan(
        user_id=1,
        book_id=1,
        due_date=datetime.utcnow() + timedelta(days=14),
        returned=False,
        status="borrowed",
    )
    seed_session.add(loan)
    seed_session.commit()
    seed_session.refresh(loan)
    loan_id = loan.id
    seed_session.close()

    calls = []
    monkeypatch.setattr(
        ServiceClient,
        "update_book_inventory",
        staticmethod(lambda book_id, delta: calls.append(delta) or {"copies_available": 1}),
    )

    def return_loan_from_thread():
        db = session_factory()
        try:
            return LoanService.return_loan(db, loan_id)
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: return_loan_from_thread(), range(2)))

    assert all(result is not None and result.returned for result in results)
    assert calls == [1]
