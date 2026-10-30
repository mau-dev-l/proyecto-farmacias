from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import Alert
from app.models.entities import AlertType, LotStatus
from app.repositories import alerts as alerts_repository
from app.repositories import branches as branches_repository
from app.repositories import lots as lots_repository


def run(db: Session, branch_id: int | None = None) -> int:
    """Generate expiration alerts and mark expired lots.

    The operation is idempotent: the unique key (lot, type, threshold) is checked
    before inserting, so running the job repeatedly does not duplicate alerts.
    Branches without an explicit configuration use the default 30-day threshold.
    Returns the number of alerts created.
    """
    today = date.today()
    thresholds_by_branch: dict[int, list[int]] = {
        branch.id: [30] for branch in branches_repository.list_all(db)
    }
    for configuration in alerts_repository.list_all_configurations(db):
        if configuration.branch_id not in thresholds_by_branch:
            thresholds_by_branch[configuration.branch_id] = []
        if configuration.lead_days not in thresholds_by_branch[configuration.branch_id]:
            thresholds_by_branch[configuration.branch_id].append(configuration.lead_days)

    created = 0
    for lot in lots_repository.list_all_active_with_stock(db):
        if branch_id is not None and lot.branch_id != branch_id:
            continue

        if lot.expiration_date < today:
            lot.status = LotStatus.EXPIRED
            if alerts_repository.get_existing(db, lot.id, AlertType.EXPIRED, None) is None:
                alerts_repository.add(
                    db,
                    Alert(lot_id=lot.id, alert_type=AlertType.EXPIRED, threshold_days=None),
                )
                created += 1
            continue

        for threshold in thresholds_by_branch.get(lot.branch_id, []):
            if lot.expiration_date > today + timedelta(days=threshold):
                continue
            if alerts_repository.get_existing(db, lot.id, AlertType.EXPIRING, threshold) is None:
                alerts_repository.add(
                    db,
                    Alert(
                        lot_id=lot.id,
                        alert_type=AlertType.EXPIRING,
                        threshold_days=threshold,
                    ),
                )
                created += 1

    db.commit()
    return created
