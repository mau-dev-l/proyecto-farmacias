from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models import User
from app.models.entities import AlertType
from app.schemas.alerts import (
    AlertConfigurationRequest,
    AlertConfigurationResponse,
    AlertResponse,
)
from app.services import alert_service

router = APIRouter(tags=["alerts"])


@router.get("/alertas", response_model=list[AlertResponse])
def list_alerts(
    alert_type: AlertType | None = Query(default=None, alias="tipo"),
    read: bool | None = Query(default=None, alias="leida"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AlertResponse]:
    return alert_service.list_alerts(db, current_user, alert_type, read)


@router.patch("/alertas/{alert_id}/leida", response_model=AlertResponse)
def mark_alert_read(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AlertResponse:
    return alert_service.mark_read(db, current_user, alert_id)


@router.post("/alertas/generar")
def generate_alerts(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    created = alert_service.generate_alerts(db, branch_id=current_user.branch_id)
    return {"created": created}


@router.get("/alertas/configuracion", response_model=AlertConfigurationResponse)
def get_alert_configuration(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AlertConfigurationResponse:
    return alert_service.get_configuration(db, current_user)


@router.put("/alertas/configuracion", response_model=AlertConfigurationResponse)
def set_alert_configuration(
    payload: AlertConfigurationRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AlertConfigurationResponse:
    return alert_service.set_configuration(db, current_user, payload)
