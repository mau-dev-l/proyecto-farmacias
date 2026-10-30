from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Alert, Lot, Movement, User
from app.models.entities import AlertType, LotStatus, MovementType
from tests.conftest import auth_headers


def test_alert_list_mark_read_and_configuration(
    client: TestClient,
    db: Session,
    admin: User,
    lots,
) -> None:
    alert = Alert(lot_id=lots[0].id, alert_type=AlertType.EXPIRING, threshold_days=30)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    headers = auth_headers(admin)

    listed = client.get("/api/v1/alertas?leida=false", headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [alert.id]

    marked = client.patch(f"/api/v1/alertas/{alert.id}/leida", headers=headers)
    assert marked.status_code == 200
    assert marked.json()["read"] is True

    default_config = client.get("/api/v1/alertas/configuracion", headers=headers)
    assert default_config.json()["lead_days"] == 30

    updated = client.put(
        "/api/v1/alertas/configuracion",
        headers=headers,
        json={"lead_days": 60},
    )
    assert updated.status_code == 200
    assert updated.json()["lead_days"] == 60


def test_reports_return_inventory_waste_and_expiring(
    client: TestClient,
    db: Session,
    admin: User,
    medicine,
    lots,
) -> None:
    waste = Movement(
        lot_id=lots[0].id,
        user_id=admin.id,
        movement_type=MovementType.WASTE,
        quantity=2,
        lot_balance=3,
        unit_cost=Decimal("2000.00"),
        created_at=datetime.now(timezone.utc),
    )
    db.add(waste)
    db.commit()
    headers = auth_headers(admin)

    inventory = client.get("/api/v1/reportes/inventario", headers=headers)
    assert inventory.status_code == 200
    assert inventory.json()["total_units"] == 25
    assert inventory.json()["medicine_count"] == 1

    waste_report = client.get("/api/v1/reportes/mermas", headers=headers)
    assert waste_report.status_code == 200
    assert waste_report.json()["quantity"] == 2
    assert waste_report.json()["total_value"] == "4000.00"

    expiring = client.get("/api/v1/reportes/proximos-vencer?days=30", headers=headers)
    assert expiring.status_code == 200
    assert [item["lot_number"] for item in expiring.json()] == ["LOTE-A"]
    assert expiring.json()[0]["days_remaining"] == 15

    dashboard = client.get("/api/v1/reportes/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["total_units"] == 25
    assert dashboard.json()["expiring_lots"] == 1


def test_multiple_alert_thresholds_are_persisted(
    client: TestClient,
    admin: User,
) -> None:
    headers = auth_headers(admin)

    updated = client.put(
        "/api/v1/alertas/configuracion",
        headers=headers,
        json={"thresholds": [30, 90, 60, 30]},
    )

    assert updated.status_code == 200
    assert updated.json()["thresholds"] == [90, 60, 30]
    assert updated.json()["lead_days"] == 90

    fetched = client.get("/api/v1/alertas/configuracion", headers=headers)
    assert fetched.json()["thresholds"] == [90, 60, 30]


def test_invalid_alert_threshold_is_rejected(client: TestClient, admin: User) -> None:
    response = client.put(
        "/api/v1/alertas/configuracion",
        headers=auth_headers(admin),
        json={"thresholds": [0, 30]},
    )

    assert response.status_code == 422


def test_alert_job_is_idempotent_and_marks_expired_lots(
    client: TestClient,
    db: Session,
    admin: User,
    lots,
) -> None:
    headers = auth_headers(admin)
    client.put(
        "/api/v1/alertas/configuracion",
        headers=headers,
        json={"thresholds": [60, 30]},
    )

    first = client.post("/api/v1/alertas/generar", headers=headers)
    assert first.status_code == 200
    assert first.json()["created"] == 2

    second = client.post("/api/v1/alertas/generar", headers=headers)
    assert second.json()["created"] == 0

    expired = Lot(
        medicine_id=lots[0].medicine_id,
        branch_id=lots[0].branch_id,
        lot_number="VENCIDO-JOB",
        expiration_date=date.today() - timedelta(days=1),
        current_quantity=3,
        unit_cost=lots[0].unit_cost,
        status=LotStatus.ACTIVE,
    )
    db.add(expired)
    db.commit()
    db.refresh(expired)

    third = client.post("/api/v1/alertas/generar", headers=headers)
    assert third.json()["created"] == 1
    db.refresh(expired)
    assert expired.status == LotStatus.EXPIRED

    expired_alert = db.query(Alert).filter(
        Alert.lot_id == expired.id,
        Alert.alert_type == AlertType.EXPIRED,
    ).one()
    assert expired_alert.threshold_days is None


def test_alert_list_is_enriched_with_lot_data(
    client: TestClient,
    db: Session,
    admin: User,
    medicine,
    lots,
) -> None:
    alert = Alert(lot_id=lots[0].id, alert_type=AlertType.EXPIRING, threshold_days=30)
    db.add(alert)
    db.commit()
    db.refresh(alert)

    response = client.get("/api/v1/alertas", headers=auth_headers(admin))

    assert response.status_code == 200
    body = response.json()[0]
    assert body["medicine_name"] == medicine.name
    assert body["lot_number"] == "LOTE-A"
    assert body["days_remaining"] == 15
    assert body["quantity"] == 5


def test_waste_report_groups_by_medicine(
    client: TestClient,
    db: Session,
    admin: User,
    branch,
    medicine,
    lots,
) -> None:
    from app.models import Medicine

    second = Medicine(
        barcode="779000000099",
        name="Amoxicilina 500 mg",
        sale_price=Decimal("5000.00"),
        minimum_stock=5,
    )
    db.add(second)
    db.commit()
    db.refresh(second)
    second_lot = Lot(
        medicine_id=second.id,
        branch_id=branch.id,
        lot_number="AMOX-1",
        expiration_date=date.today() + timedelta(days=20),
        current_quantity=10,
        unit_cost=Decimal("3000.00"),
        status=LotStatus.ACTIVE,
    )
    db.add(second_lot)
    db.commit()
    db.refresh(second_lot)

    db.add_all(
        [
            Movement(
                lot_id=lots[0].id,
                user_id=admin.id,
                movement_type=MovementType.WASTE,
                quantity=2,
                lot_balance=3,
                unit_cost=Decimal("2000.00"),
            ),
            Movement(
                lot_id=second_lot.id,
                user_id=admin.id,
                movement_type=MovementType.WASTE,
                quantity=1,
                lot_balance=9,
                unit_cost=Decimal("3000.00"),
            ),
        ]
    )
    db.commit()

    response = client.get("/api/v1/reportes/mermas", headers=auth_headers(admin))

    assert response.status_code == 200
    body = response.json()
    assert body["quantity"] == 3
    assert body["total_value"] == "7000.00"
    assert [item["medicine_name"] for item in body["items"]] == [
        "Ibuprofeno 400 mg",
        "Amoxicilina 500 mg",
    ]


def test_movements_report_and_invalid_range(
    client: TestClient,
    db: Session,
    admin: User,
    medicine,
    lots,
) -> None:
    db.add(
        Movement(
            lot_id=lots[0].id,
            user_id=admin.id,
            movement_type=MovementType.ENTRY,
            quantity=5,
            lot_balance=5,
            unit_cost=lots[0].unit_cost,
            created_at=datetime(2026, 2, 1, 10, 0),
        )
    )
    db.commit()
    headers = auth_headers(admin)

    report = client.get("/api/v1/reportes/movimientos", headers=headers)
    assert report.status_code == 200
    assert report.json()[0]["lot_number"] == "LOTE-A"

    invalid = client.get(
        "/api/v1/reportes/mermas?desde=2026-03-01&hasta=2026-02-01",
        headers=headers,
    )
    assert invalid.status_code == 400
    assert invalid.json()["detail"] == "End date cannot be earlier than start date"


def test_export_inventory_csv(client: TestClient, admin: User, medicine, lots) -> None:
    response = client.get(
        "/api/v1/reportes/exportar?tipo=inventario",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'filename="inventario.csv"' in response.headers["content-disposition"]
    lines = response.text.strip().splitlines()
    assert lines[0] == "medicine_id,name,barcode,minimum_stock,total_stock"
    assert "Ibuprofeno 400 mg" in lines[1]


def test_export_rejects_unknown_report_type(client: TestClient, admin: User) -> None:
    response = client.get(
        "/api/v1/reportes/exportar?tipo=otro",
        headers=auth_headers(admin),
    )

    assert response.status_code == 422
