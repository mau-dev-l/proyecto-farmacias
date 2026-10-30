from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Medicine, User
from tests.conftest import auth_headers


def test_create_list_search_and_barcode(client: TestClient, admin: User) -> None:
    headers = auth_headers(admin)
    created = client.post(
        "/api/v1/medicamentos",
        headers=headers,
        json={
            "barcode": "779000000002",
            "name": "Paracetamol 500 mg",
            "active_ingredient": "Paracetamol",
            "presentation": "Caja x 10",
            "sale_price": "3200.50",
            "minimum_stock": 5,
        },
    )

    assert created.status_code == 201
    medicine_id = created.json()["id"]

    listed = client.get("/api/v1/medicamentos?q=paracetamol", headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [medicine_id]

    by_barcode = client.get("/api/v1/medicamentos/barcode/779000000002", headers=headers)
    assert by_barcode.status_code == 200
    assert by_barcode.json()["name"] == "Paracetamol 500 mg"


def test_duplicate_barcode_returns_conflict(client: TestClient, admin: User, medicine: Medicine) -> None:
    response = client.post(
        "/api/v1/medicamentos",
        headers=auth_headers(admin),
        json={
            "barcode": medicine.barcode,
            "name": "Duplicado",
            "sale_price": "1000.00",
            "minimum_stock": 1,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Barcode already exists"


def test_update_and_deactivate_medicine(client: TestClient, db: Session, admin: User, medicine: Medicine) -> None:
    headers = auth_headers(admin)
    updated = client.put(
        f"/api/v1/medicamentos/{medicine.id}",
        headers=headers,
        json={"name": "Ibuprofeno 600 mg", "minimum_stock": 15},
    )

    assert updated.status_code == 200
    assert updated.json()["name"] == "Ibuprofeno 600 mg"
    assert updated.json()["minimum_stock"] == 15

    deleted = client.delete(f"/api/v1/medicamentos/{medicine.id}", headers=headers)
    assert deleted.status_code == 204
    db.refresh(medicine)
    assert medicine.active is False

    listed = client.get("/api/v1/medicamentos", headers=headers)
    assert listed.json() == []


def test_barcode_not_found(client: TestClient, admin: User) -> None:
    response = client.get("/api/v1/medicamentos/barcode/000000", headers=auth_headers(admin))

    assert response.status_code == 404


def test_list_medicines_returns_total_count_header(client: TestClient, admin: User, medicine) -> None:
    response = client.get("/api/v1/medicamentos?page=1&page_size=1", headers=auth_headers(admin))

    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "1"
    assert len(response.json()) == 1


def test_search_matches_name_or_barcode(client: TestClient, admin: User, medicine) -> None:
    headers = auth_headers(admin)

    by_barcode = client.get(f"/api/v1/medicamentos?q={medicine.barcode}", headers=headers)
    by_name = client.get("/api/v1/medicamentos?q=ibuprofeno", headers=headers)

    assert [item["id"] for item in by_barcode.json()] == [medicine.id]
    assert [item["id"] for item in by_name.json()] == [medicine.id]


def test_barcode_lookup_includes_stock_and_lots(client: TestClient, admin: User, medicine, lots) -> None:
    response = client.get(
        f"/api/v1/medicamentos/barcode/{medicine.barcode}",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_stock"] == 25
    assert [lot["lot_number"] for lot in body["lots"]] == ["LOTE-A", "LOTE-B"]
