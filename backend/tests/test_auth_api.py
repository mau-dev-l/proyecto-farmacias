from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User
from tests.conftest import auth_headers


def test_login_returns_token_and_me_returns_user(client: TestClient, admin: User) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@farmacia.com", "password": "Farmacia123"},
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "admin@farmacia.com"
    assert me.json()["role"] == "ADMIN"


def test_login_rejects_wrong_password(client: TestClient, admin: User) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@farmacia.com", "password": "Incorrecta123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_rejects_inactive_user(client: TestClient, db: Session, admin: User) -> None:
    admin.active = False
    db.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@farmacia.com", "password": "Farmacia123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Inactive user"


def test_five_failed_attempts_lock_account(client: TestClient, db: Session, admin: User) -> None:
    for _ in range(5):
        client.post(
            "/api/v1/auth/login",
            json={"email": "admin@farmacia.com", "password": "Incorrecta123"},
        )

    db.refresh(admin)
    assert admin.locked_until is not None

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@farmacia.com", "password": "Farmacia123"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Account temporarily locked"


def test_successful_login_resets_failed_attempts(client: TestClient, db: Session, admin: User) -> None:
    for _ in range(2):
        client.post(
            "/api/v1/auth/login",
            json={"email": "admin@farmacia.com", "password": "Incorrecta123"},
        )

    db.refresh(admin)
    assert admin.failed_attempts == 2

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@farmacia.com", "password": "Farmacia123"},
    )

    assert response.status_code == 200
    db.refresh(admin)
    assert admin.failed_attempts == 0
    assert admin.locked_until is None


def test_me_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_employee_cannot_delete_medicine(client: TestClient, employee: User, medicine) -> None:
    response = client.delete(
        f"/api/v1/medicamentos/{medicine.id}",
        headers=auth_headers(employee),
    )

    assert response.status_code == 403
