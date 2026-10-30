from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Alert, AlertConfiguration, Lot, Medicine
from app.models.entities import AlertType


def list_for_branch(
    db: Session,
    branch_id: int,
    alert_type: AlertType | None = None,
    read: bool | None = None,
) -> list:
    query = (
        select(
            Alert.id,
            Alert.lot_id,
            Alert.alert_type,
            Alert.threshold_days,
            Alert.read,
            Alert.created_at,
            Medicine.name.label("medicine_name"),
            Lot.lot_number,
            Lot.expiration_date,
            Lot.current_quantity.label("quantity"),
        )
        .join(Lot, Alert.lot_id == Lot.id)
        .join(Medicine, Lot.medicine_id == Medicine.id)
        .where(Lot.branch_id == branch_id)
        .order_by(Alert.created_at.desc(), Alert.id.desc())
    )
    if alert_type is not None:
        query = query.where(Alert.alert_type == alert_type)
    if read is not None:
        query = query.where(Alert.read == read)
    return list(db.execute(query))


def get_for_branch(db: Session, alert_id: int, branch_id: int) -> Alert | None:
    return db.scalar(
        select(Alert)
        .join(Lot, Alert.lot_id == Lot.id)
        .where(Alert.id == alert_id, Lot.branch_id == branch_id)
    )


def get_detail(db: Session, alert_id: int, branch_id: int):
    return db.execute(
        select(
            Alert.id,
            Alert.lot_id,
            Alert.alert_type,
            Alert.threshold_days,
            Alert.read,
            Alert.created_at,
            Medicine.name.label("medicine_name"),
            Lot.lot_number,
            Lot.expiration_date,
            Lot.current_quantity.label("quantity"),
        )
        .join(Lot, Alert.lot_id == Lot.id)
        .join(Medicine, Lot.medicine_id == Medicine.id)
        .where(Alert.id == alert_id, Lot.branch_id == branch_id)
    ).first()


def get_existing(
    db: Session,
    lot_id: int,
    alert_type: AlertType,
    threshold_days: int | None,
) -> Alert | None:
    return db.scalar(
        select(Alert).where(
            Alert.lot_id == lot_id,
            Alert.alert_type == alert_type,
            Alert.threshold_days.is_(threshold_days) if threshold_days is None else Alert.threshold_days == threshold_days,
        )
    )


def list_configurations(db: Session, branch_id: int) -> list[AlertConfiguration]:
    return list(
        db.scalars(
            select(AlertConfiguration)
            .where(AlertConfiguration.branch_id == branch_id)
            .order_by(AlertConfiguration.lead_days.desc())
        )
    )


def list_all_configurations(db: Session) -> list[AlertConfiguration]:
    return list(
        db.scalars(
            select(AlertConfiguration).order_by(
                AlertConfiguration.branch_id,
                AlertConfiguration.lead_days.desc(),
            )
        )
    )


def delete_configurations(db: Session, branch_id: int) -> None:
    for configuration in list_configurations(db, branch_id):
        db.delete(configuration)


def add_configuration(db: Session, configuration: AlertConfiguration) -> AlertConfiguration:
    db.add(configuration)
    return configuration


def exists_unread(db: Session, lot_id: int, alert_type: AlertType) -> bool:
    return (
        db.scalar(
            select(Alert.id).where(
                Alert.lot_id == lot_id,
                Alert.alert_type == alert_type,
                Alert.read.is_(False),
            )
        )
        is not None
    )


def exists_unread_for_medicine(db: Session, medicine_id: int, alert_type: AlertType) -> bool:
    return (
        db.scalar(
            select(Alert.id)
            .join(Lot, Alert.lot_id == Lot.id)
            .where(
                Lot.medicine_id == medicine_id,
                Alert.alert_type == alert_type,
                Alert.read.is_(False),
            )
        )
        is not None
    )


def add(db: Session, alert: Alert) -> Alert:
    db.add(alert)
    return alert
