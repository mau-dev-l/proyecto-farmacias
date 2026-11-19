from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Branch, TelegramLink, TelegramLinkCode, User
from tests.conftest import auth_headers


def test_link_code_requires_session(client: TestClient) -> None:
    response = client.post("/api/v1/telegram/codigo")

    assert response.status_code == 401


def test_link_code_returns_single_use_code(
    client: TestClient,
    admin: User,
    db: Session,
) -> None:
    response = client.post(
        "/api/v1/telegram/codigo",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    body = response.json()
    codigo = body["codigo"]

    assert len(codigo) == 10
    assert codigo.upper() == codigo
    assert codigo.isalnum()
    assert body["expira_en"]

    stored = (
        db.query(TelegramLinkCode)
        .filter(TelegramLinkCode.user_id == admin.id)
        .all()
    )

    assert len(stored) == 1
    assert stored[0].used is False
    assert stored[0].code != codigo
    assert len(stored[0].code) == 64


def test_new_code_invalidates_previous_code(
    client: TestClient,
    admin: User,
    db: Session,
) -> None:
    first = client.post(
        "/api/v1/telegram/codigo",
        headers=auth_headers(admin),
    )
    second = client.post(
        "/api/v1/telegram/codigo",
        headers=auth_headers(admin),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["codigo"] != second.json()["codigo"]

    stored = (
        db.query(TelegramLinkCode)
        .filter(TelegramLinkCode.user_id == admin.id)
        .order_by(TelegramLinkCode.id)
        .all()
    )

    assert len(stored) == 2
    assert stored[0].used is True
    assert stored[1].used is False


def test_link_code_rejects_inactive_branch(
    client: TestClient,
    admin: User,
    branch: Branch,
    db: Session,
) -> None:
    branch.active = False
    db.commit()

    response = client.post(
        "/api/v1/telegram/codigo",
        headers=auth_headers(admin),
    )

    assert response.status_code == 400


def test_link_status_reports_pending_and_linked_accounts(
    client: TestClient,
    admin: User,
    db: Session,
) -> None:
    pending = client.get(
        "/api/v1/telegram/estado",
        headers=auth_headers(admin),
    )

    assert pending.status_code == 200
    assert pending.json()["vinculado"] is False

    db.add(TelegramLink(user_id=admin.id, chat_id=987654321))
    db.commit()

    linked = client.get(
        "/api/v1/telegram/estado",
        headers=auth_headers(admin),
    )

    assert linked.status_code == 200
    assert linked.json()["vinculado"] is True
    assert linked.json()["vinculado_en"]
