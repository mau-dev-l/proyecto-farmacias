from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models import Alert, AlertConfiguration, Lot, Medicine, User
from app.models.entities import AlertType, LotStatus
from app.schemas.alerts import AlertConfigurationRequest, AlertConfigurationResponse, AlertResponse

router = APIRouter(tags=["alerts"])


@router.get("/alertas", response_model=list[AlertResponse])
def list_alerts(
    alert_type: AlertType | None = Query(default=None, alias="tipo"),
    read: bool | None = Query(default=None, alias="leida"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Alert]:
    query = select(Alert).join(Lot, Alert.lot_id == Lot.id).where(Lot.branch_id == current_user.branch_id).order_by(Alert.created_at.desc())
    if alert_type is not None:
        query = query.where(Alert.alert_type == alert_type)
    if read is not None:
        query = query.where(Alert.read == read)
    return list(db.scalars(query))


@router.patch("/alertas/{alert_id}/leida", response_model=AlertResponse)
def mark_alert_read(alert_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Alert:
    alert = db.scalar(select(Alert).join(Lot, Alert.lot_id == Lot.id).where(Alert.id == alert_id, Lot.branch_id == current_user.branch_id))
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    alert.read = True
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/alertas/configuracion", response_model=AlertConfigurationResponse)
def get_alert_configuration(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AlertConfigurationResponse:
    config = db.scalar(select(AlertConfiguration).where(AlertConfiguration.branch_id == current_user.branch_id).order_by(AlertConfiguration.lead_days.desc()))
    return AlertConfigurationResponse(branch_id=current_user.branch_id, lead_days=config.lead_days if config else 30)


@router.put("/alertas/configuracion", response_model=AlertConfigurationResponse)
def set_alert_configuration(payload: AlertConfigurationRequest, current_user: User = Depends(require_admin), db: Session = Depends(get_db)) -> AlertConfigurationResponse:
    config = db.scalar(select(AlertConfiguration).where(AlertConfiguration.branch_id == current_user.branch_id).order_by(AlertConfiguration.lead_days.desc()))
    if config is None:
        config = AlertConfiguration(branch_id=current_user.branch_id, lead_days=payload.lead_days)
        db.add(config)
    else:
        config.lead_days = payload.lead_days
    db.commit()
    return AlertConfigurationResponse(branch_id=current_user.branch_id, lead_days=payload.lead_days)
