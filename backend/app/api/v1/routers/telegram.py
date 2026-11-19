from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.telegram import LinkCodeResponse, LinkStatusResponse
from app.services import telegram_service

router = APIRouter(prefix="/telegram", tags=["telegram"])
bot_router = APIRouter(prefix="/bot", tags=["telegram"])


@router.post("/codigo", response_model=LinkCodeResponse)
def create_link_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LinkCodeResponse:
    try:
        codigo = telegram_service.crear_codigo_vinculacion(db, current_user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return LinkCodeResponse(
        codigo=codigo.codigo,
        expira_en=codigo.expira_en,
    )


@router.get("/estado", response_model=LinkStatusResponse)
def get_link_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LinkStatusResponse:
    estado = telegram_service.obtener_estado_vinculacion(db, current_user)
    username = settings.telegram_bot_username.strip() or None

    return LinkStatusResponse(
        vinculado=estado.vinculado,
        vinculado_en=estado.vinculado_en,
        bot_username=username,
    )


@router.post("/vincular")
def link_chat() -> None:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="El bot valida los codigos directamente contra la base de datos",
    )


@bot_router.post("/consulta")
def bot_query() -> None:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="LLM integration is deferred",
    )
