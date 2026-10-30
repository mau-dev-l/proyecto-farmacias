from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import Alert, AlertConfiguration, User
from app.models.entities import AlertType
from app.repositories import alerts as alerts_repository
from app.schemas.alerts import AlertConfigurationRequest, AlertConfigurationResponse, AlertResponse
from app.services import alert_job_service


def _to_response(row, today: date) -> AlertResponse:
    return AlertResponse(
        id=row.id,
        lot_id=row.lot_id,
        alert_type=row.alert_type,
        threshold_days=row.threshold_days,
        read=row.read,
        created_at=row.created_at,
        medicine_name=row.medicine_name,
        lot_number=row.lot_number,
        expiration_date=row.expiration_date,
        days_remaining=(row.expiration_date - today).days,
        quantity=row.quantity,
    )


def list_alerts(
    db: Session,
    current_user: User,
    alert_type: AlertType | None,
    read: bool | None,
) -> list[AlertResponse]:
    today = date.today()
    rows = alerts_repository.list_for_branch(db, current_user.branch_id, alert_type, read)
    return [_to_response(row, today) for row in rows]


def mark_read(db: Session, current_user: User, alert_id: int) -> AlertResponse:
    alert = alerts_repository.get_for_branch(db, alert_id, current_user.branch_id)
    if alert is None:
        raise NotFoundError("Alert not found")
    alert.read = True
    db.commit()
    row = alerts_repository.get_detail(db, alert_id, current_user.branch_id)
    return _to_response(row, date.today())


def _to_configuration(branch_id: int, thresholds: list[int]) -> AlertConfigurationResponse:
    return AlertConfigurationResponse(
        branch_id=branch_id,
        lead_days=max(thresholds),
        thresholds=thresholds,
    )


def get_configuration(db: Session, current_user: User) -> AlertConfigurationResponse:
    configurations = alerts_repository.list_configurations(db, current_user.branch_id)
    thresholds = [configuration.lead_days for configuration in configurations] or [30]
    return _to_configuration(current_user.branch_id, sorted(thresholds, reverse=True))


def set_configuration(
    db: Session,
    current_user: User,
    payload: AlertConfigurationRequest,
) -> AlertConfigurationResponse:
    thresholds = payload.thresholds or [30]
    alerts_repository.delete_configurations(db, current_user.branch_id)
    db.flush()
    for threshold in thresholds:
        alerts_repository.add_configuration(
            db,
            AlertConfiguration(branch_id=current_user.branch_id, lead_days=threshold),
        )
    db.commit()
    return _to_configuration(current_user.branch_id, thresholds)


def generate_alerts(db: Session, branch_id: int | None = None) -> int:
    """Create expiration alerts without duplicating existing ones.

    Returns the number of alerts created.
    """
    return alert_job_service.run(db, branch_id=branch_id)
