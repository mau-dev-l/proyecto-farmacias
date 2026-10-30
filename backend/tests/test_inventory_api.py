from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Alert, Lot, Movement, User
from app.models.entities import AlertType, LotStatus, MovementType
from tests.conftest import auth_headers


def test_entry_creates_lot_and_movement(client: TestClient, db: Session, admin: User, medicine) -> None:
    response = client.post(
        "/api/v1/movimientos/entrada",
        headers=auth_headers(admin),
        json={
            "medicine_id": medicine.id,
            "lot_number": "NUEVO-1",
            "expiration_date": str(date.today() + timedelta(days=180)),
            "quantity": 12,
            "unit_cost": "1500.00",
        },
    )

    assert response.status_code == 201
    assert response.json()["movement_type"] == "ENTRADA"
    assert response.json()["lot_balance"] == 12

    lot = db.scalar(select(Lot).where(Lot.lot_number == "NUEVO-1"))
    assert lot is not None
    assert lot.current_quantity == 12


def test_entry_adds_quantity_to_existing_lot(client: TestClient, db: Session, admin: User, medicine, lots) -> None:
    response = client.post(
        "/api/v1/movimientos/entrada",
        headers=auth_headers(admin),
        json={
            "medicine_id": medicine.id,
            "lot_number": lots[0].lot_number,
            "expiration_date": str(lots[0].expiration_date),
            "quantity": 3,
            "unit_cost": "9999.00",
        },
    )

    assert response.status_code == 201
    db.refresh(lots[0])
    assert lots[0].current_quantity == 8
    assert str(lots[0].unit_cost) == "2000.00"


def test_peps_suggestion_orders_by_expiration(client: TestClient, admin: User, medicine, lots) -> None:
    response = client.get(
        f"/api/v1/movimientos/peps-sugerido?medicine_id={medicine.id}&quantity=8",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200
    assert [item["lot_number"] for item in response.json()] == ["LOTE-A", "LOTE-B"]
    assert [item["suggested_quantity"] for item in response.json()] == [5, 3]


def test_sale_deducts_fefo_and_records_one_movement_per_lot(
    client: TestClient,
    db: Session,
    admin: User,
    medicine,
    lots,
) -> None:
    response = client.post(
        "/api/v1/movimientos/salida",
        headers=auth_headers(admin),
        json={"medicine_id": medicine.id, "quantity": 8},
    )

    assert response.status_code == 200
    assert [(item["lot_id"], item["quantity"]) for item in response.json()] == [
        (lots[0].id, 5),
        (lots[1].id, 3),
    ]
    db.refresh(lots[0])
    db.refresh(lots[1])
    assert lots[0].current_quantity == 0
    assert lots[1].current_quantity == 17


def test_sale_rejects_insufficient_stock(client: TestClient, db: Session, admin: User, medicine, lots) -> None:
    response = client.post(
        "/api/v1/movimientos/salida",
        headers=auth_headers(admin),
        json={"medicine_id": medicine.id, "quantity": 500},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient non-expired stock"
    db.refresh(lots[0])
    assert lots[0].current_quantity == 5


def test_kardex_lists_movements(client: TestClient, db: Session, admin: User, medicine, lots) -> None:
    movement = Movement(
        lot_id=lots[0].id,
        user_id=admin.id,
        movement_type=MovementType.ENTRY,
        quantity=5,
        lot_balance=5,
        unit_cost=lots[0].unit_cost,
    )
    db.add(movement)
    db.commit()

    response = client.get(
        f"/api/v1/kardex?medicine_id={medicine.id}",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["movement_type"] == "ENTRADA"


def test_inventory_shows_stock_and_lots(client: TestClient, admin: User, medicine, lots) -> None:
    inventory = client.get("/api/v1/inventario", headers=auth_headers(admin))
    assert inventory.status_code == 200
    assert inventory.json()[0]["total_stock"] == 25
    assert [lot["lot_number"] for lot in inventory.json()[0]["lots"]] == ["LOTE-A", "LOTE-B"]

    lot_list = client.get(
        f"/api/v1/medicamentos/{medicine.id}/lotes",
        headers=auth_headers(admin),
    )
    assert lot_list.status_code == 200
    assert [item["lot_number"] for item in lot_list.json()] == ["LOTE-A", "LOTE-B"]


def test_inventory_search_matches_barcode(client: TestClient, admin: User, medicine, lots) -> None:
    response = client.get(f"/api/v1/inventario?q={medicine.barcode}", headers=auth_headers(admin))

    assert response.status_code == 200
    assert [item["medicine_id"] for item in response.json()] == [medicine.id]


def test_entry_rejects_past_expiration(client: TestClient, admin: User, medicine) -> None:
    response = client.post(
        "/api/v1/movimientos/entrada",
        headers=auth_headers(admin),
        json={
            "medicine_id": medicine.id,
            "lot_number": "VENCIDO-1",
            "expiration_date": str(date.today() - timedelta(days=1)),
            "quantity": 5,
            "unit_cost": "1000.00",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Expiration date cannot be in the past"


def test_entry_rejects_same_lot_with_different_expiration(
    client: TestClient,
    admin: User,
    medicine,
    lots,
) -> None:
    response = client.post(
        "/api/v1/movimientos/entrada",
        headers=auth_headers(admin),
        json={
            "medicine_id": medicine.id,
            "lot_number": lots[0].lot_number,
            "expiration_date": str(lots[0].expiration_date + timedelta(days=30)),
            "quantity": 5,
            "unit_cost": "1000.00",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Lot number already exists with a different expiration date"


def test_entry_rejects_unknown_supplier(client: TestClient, admin: User, medicine) -> None:
    response = client.post(
        "/api/v1/movimientos/entrada",
        headers=auth_headers(admin),
        json={
            "medicine_id": medicine.id,
            "lot_number": "CON-PROVEEDOR",
            "expiration_date": str(date.today() + timedelta(days=120)),
            "quantity": 5,
            "unit_cost": "1000.00",
            "supplier_id": 9999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Supplier not found"


def test_manual_lot_override_requires_reason(
    client: TestClient,
    db: Session,
    admin: User,
    medicine,
    lots,
) -> None:
    headers = auth_headers(admin)
    payload = {"medicine_id": medicine.id, "quantity": 3, "lot_id": lots[1].id}

    rejected = client.post("/api/v1/movimientos/salida", headers=headers, json=payload)
    assert rejected.status_code == 400
    assert rejected.json()["detail"] == "A reason is required to override the PEPS suggestion"

    accepted = client.post(
        "/api/v1/movimientos/salida",
        headers=headers,
        json={**payload, "reason": "Cliente solicitó lote específico"},
    )
    assert accepted.status_code == 200
    db.refresh(lots[0])
    db.refresh(lots[1])
    assert lots[0].current_quantity == 5
    assert lots[1].current_quantity == 17


def test_waste_consumes_expired_lots_first(
    client: TestClient,
    db: Session,
    admin: User,
    medicine,
    lots,
) -> None:
    expired = Lot(
        medicine_id=medicine.id,
        branch_id=lots[0].branch_id,
        lot_number="VENCIDO",
        expiration_date=date.today() - timedelta(days=5),
        current_quantity=4,
        unit_cost=lots[0].unit_cost,
        status=LotStatus.ACTIVE,
    )
    db.add(expired)
    db.commit()
    db.refresh(expired)

    response = client.post(
        "/api/v1/movimientos/salida",
        headers=auth_headers(admin),
        json={"medicine_id": medicine.id, "quantity": 4, "movement_type": "SALIDA_MERMA"},
    )

    assert response.status_code == 200
    assert response.json()[0]["lot_id"] == expired.id
    assert response.json()[0]["movement_type"] == "SALIDA_MERMA"


def test_sale_cannot_consume_expired_lot(
    client: TestClient,
    db: Session,
    admin: User,
    medicine,
    lots,
) -> None:
    expired = Lot(
        medicine_id=medicine.id,
        branch_id=lots[0].branch_id,
        lot_number="VENCIDO-2",
        expiration_date=date.today() - timedelta(days=5),
        current_quantity=4,
        unit_cost=lots[0].unit_cost,
        status=LotStatus.ACTIVE,
    )
    db.add(expired)
    db.commit()
    db.refresh(expired)

    response = client.post(
        "/api/v1/movimientos/salida",
        headers=auth_headers(admin),
        json={
            "medicine_id": medicine.id,
            "quantity": 1,
            "movement_type": "SALIDA_VENTA",
            "lot_id": expired.id,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Expired lots cannot be sold; register them as waste"


def test_sale_below_minimum_creates_one_low_stock_alert(
    client: TestClient,
    db: Session,
    admin: User,
    medicine,
    lots,
) -> None:
    headers = auth_headers(admin)

    first = client.post(
        "/api/v1/movimientos/salida",
        headers=headers,
        json={"medicine_id": medicine.id, "quantity": 20},
    )
    assert first.status_code == 200

    alerts = db.query(Alert).filter(Alert.alert_type == AlertType.LOW_STOCK).all()
    assert len(alerts) == 1
    assert alerts[0].lot_id == lots[0].id
    assert alerts[0].read is False

    second = client.post(
        "/api/v1/movimientos/salida",
        headers=headers,
        json={"medicine_id": medicine.id, "quantity": 1},
    )
    assert second.status_code == 200

    alerts = db.query(Alert).filter(Alert.alert_type == AlertType.LOW_STOCK).all()
    assert len(alerts) == 1


def test_kardex_filters_by_date_and_rejects_invalid_range(
    client: TestClient,
    db: Session,
    admin: User,
    medicine,
    lots,
) -> None:
    db.add_all(
        [
            Movement(
                lot_id=lots[0].id,
                user_id=admin.id,
                movement_type=MovementType.ENTRY,
                quantity=5,
                lot_balance=5,
                unit_cost=lots[0].unit_cost,
                created_at=datetime(2026, 1, 10, 12, 0),
            ),
            Movement(
                lot_id=lots[1].id,
                user_id=admin.id,
                movement_type=MovementType.ENTRY,
                quantity=20,
                lot_balance=20,
                unit_cost=lots[1].unit_cost,
                created_at=datetime(2026, 3, 10, 12, 0),
            ),
        ]
    )
    db.commit()
    headers = auth_headers(admin)

    filtered = client.get(
        "/api/v1/kardex?desde=2026-03-01&hasta=2026-03-31",
        headers=headers,
    )
    assert filtered.status_code == 200
    assert [item["lot_number"] for item in filtered.json()] == ["LOTE-B"]
    assert filtered.json()[0]["user_name"] == "Admin Prueba"

    invalid = client.get(
        "/api/v1/kardex?desde=2026-03-31&hasta=2026-03-01",
        headers=headers,
    )
    assert invalid.status_code == 400
    assert invalid.json()["detail"] == "End date cannot be earlier than start date"
