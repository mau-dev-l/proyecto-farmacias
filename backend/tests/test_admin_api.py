from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User
from tests.conftest import auth_headers


def test_branch_create_duplicate_and_list(client: TestClient, admin: User) -> None:
    headers = auth_headers(admin)
    created = client.post(
        "/api/v1/sucursales",
        headers=headers,
        json={"name": "Sucursal Norte", "address": "Calle 10"},
    )

    assert created.status_code == 201
    duplicate = client.post(
        "/api/v1/sucursales",
        headers=headers,
        json={"name": "Sucursal Norte"},
    )
    assert duplicate.status_code == 409

    listed = client.get("/api/v1/sucursales", headers=headers)
    assert listed.status_code == 200
    assert [item["name"] for item in listed.json()] == ["Sucursal Central", "Sucursal Norte"]


def test_admin_cannot_remove_own_admin_role(client: TestClient, admin: User) -> None:
    response = client.patch(
        f"/api/v1/usuarios/{admin.id}",
        headers=auth_headers(admin),
        json={"role": "EMPLEADO"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Administrators cannot remove their own admin role"


def test_user_update_duplicate_email_returns_conflict(
    client: TestClient,
    admin: User,
    employee: User,
) -> None:
    response = client.put(
        f"/api/v1/usuarios/{employee.id}",
        headers=auth_headers(admin),
        json={"email": "admin@farmacia.com"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already exists"


def test_branch_update_duplicate_name_returns_conflict(client: TestClient, admin: User, branch) -> None:
    headers = auth_headers(admin)
    second = client.post("/api/v1/sucursales", headers=headers, json={"name": "Sucursal Norte"})
    assert second.status_code == 201

    response = client.put(
        f"/api/v1/sucursales/{second.json()['id']}",
        headers=headers,
        json={"name": branch.name},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Branch name already exists"


def test_user_create_update_and_duplicate_email(client: TestClient, db: Session, admin: User, branch) -> None:
    headers = auth_headers(admin)
    created = client.post(
        "/api/v1/usuarios",
        headers=headers,
        json={
            "branch_id": branch.id,
            "name": "Nuevo Empleado",
            "email": "nuevo@farmacia.com",
            "password": "Farmacia123",
            "role": "EMPLEADO",
        },
    )

    assert created.status_code == 201
    user_id = created.json()["id"]

    duplicate = client.post(
        "/api/v1/usuarios",
        headers=headers,
        json={
            "branch_id": branch.id,
            "name": "Duplicado",
            "email": "nuevo@farmacia.com",
            "password": "Farmacia123",
            "role": "EMPLEADO",
        },
    )
    assert duplicate.status_code == 409

    updated = client.patch(
        f"/api/v1/usuarios/{user_id}",
        headers=headers,
        json={"active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["active"] is False
