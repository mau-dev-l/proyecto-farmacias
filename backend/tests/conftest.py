from collections.abc import Generator
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Branch, Lot, Medicine, User
from app.models.entities import LotStatus, UserRole


@pytest.fixture
def db() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def branch(db: Session) -> Branch:
    record = Branch(name="Sucursal Central", address="Av. Principal 123")
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@pytest.fixture
def admin(db: Session, branch: Branch) -> User:
    record = User(
        branch_id=branch.id,
        name="Admin Prueba",
        email="admin@farmacia.com",
        password_hash=hash_password("Farmacia123"),
        role=UserRole.ADMIN,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@pytest.fixture
def employee(db: Session, branch: Branch) -> User:
    record = User(
        branch_id=branch.id,
        name="Empleado Prueba",
        email="empleado@farmacia.com",
        password_hash=hash_password("Farmacia123"),
        role=UserRole.EMPLOYEE,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@pytest.fixture
def medicine(db: Session) -> Medicine:
    record = Medicine(
        barcode="779000000001",
        name="Ibuprofeno 400 mg",
        active_ingredient="Ibuprofeno",
        presentation="Caja x 20 comprimidos",
        sale_price=Decimal("4500.00"),
        minimum_stock=10,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@pytest.fixture
def lots(db: Session, branch: Branch, medicine: Medicine) -> list[Lot]:
    records = [
        Lot(
            medicine_id=medicine.id,
            branch_id=branch.id,
            lot_number="LOTE-A",
            expiration_date=date.today() + timedelta(days=15),
            current_quantity=5,
            unit_cost=Decimal("2000.00"),
            status=LotStatus.ACTIVE,
        ),
        Lot(
            medicine_id=medicine.id,
            branch_id=branch.id,
            lot_number="LOTE-B",
            expiration_date=date.today() + timedelta(days=90),
            current_quantity=20,
            unit_cost=Decimal("2100.00"),
            status=LotStatus.ACTIVE,
        ),
    ]
    db.add_all(records)
    db.commit()
    for record in records:
        db.refresh(record)
    return records


def auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}
