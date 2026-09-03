"""HTTP clients for external service validation in Loan Service."""

from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()


class ServiceClientError(Exception):
    """A controlled failure while calling another microservice."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class InventoryUnavailableError(ServiceClientError):
    """The requested inventory operation cannot be completed."""

    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class ServiceClient:
    @staticmethod
    def _get_client() -> httpx.Client:
        return httpx.Client(timeout=5.0)

    @staticmethod
    def get_user(user_id: int) -> dict[str, Any] | None:
        url = f"{settings.USER_SERVICE_URL}/api/v1/users/{user_id}"
        try:
            with ServiceClient._get_client() as client:
                response = client.get(
                    url,
                    headers={"X-Internal-Service-Token": settings.INTERNAL_SERVICE_TOKEN},
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as exc:
            raise ServiceClientError("User service timed out", 503) from exc
        except httpx.HTTPError as exc:
            raise ServiceClientError("User service request failed") from exc

    @staticmethod
    def get_book(book_id: int) -> dict[str, Any] | None:
        url = f"{settings.BOOK_SERVICE_URL}/api/v1/books/{book_id}"
        try:
            with ServiceClient._get_client() as client:
                response = client.get(url)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as exc:
            raise ServiceClientError("Book service timed out", 503) from exc
        except httpx.HTTPError as exc:
            raise ServiceClientError("Book service request failed") from exc

    @staticmethod
    def update_book_inventory(book_id: int, delta: int) -> dict[str, Any]:
        if delta not in (-1, 1):
            raise ValueError("Inventory changes are limited to one copy")

        operation = "decrement" if delta < 0 else "increment"
        url = f"{settings.BOOK_SERVICE_URL}/api/v1/books/{book_id}/inventory/{operation}"
        try:
            with ServiceClient._get_client() as client:
                response = client.patch(
                    url,
                    headers={"X-Internal-Service-Token": settings.INTERNAL_SERVICE_TOKEN},
                )
                if response.status_code == 404:
                    raise ValueError("Book not found")
                if response.status_code == 409:
                    raise InventoryUnavailableError("Not enough copies available")
                response.raise_for_status()
                return response.json()
        except (ValueError, InventoryUnavailableError):
            raise
        except httpx.TimeoutException as exc:
            raise ServiceClientError("Book inventory service timed out", 503) from exc
        except httpx.HTTPError as exc:
            raise ServiceClientError("Book inventory update failed") from exc
