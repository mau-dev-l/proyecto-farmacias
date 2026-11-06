from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Branch, TelegramLink, User


@dataclass(frozen=True)
class IdentidadTelegram:
    usuario_id: int
    sucursal_id: int


def obtener_identidad_telegram(
    db: Session,
    chat_id: int,
) -> IdentidadTelegram | None:
    """Obtiene la identidad autorizada de un chat vinculado."""

    if (
        isinstance(chat_id, bool)
        or not isinstance(chat_id, int)
        or chat_id <= 0
    ):
        return None

    resultado = (
        db.query(User.id, Branch.id)
        .join(
            TelegramLink,
            TelegramLink.user_id == User.id,
        )
        .join(
            Branch,
            User.branch_id == Branch.id,
        )
        .filter(
            TelegramLink.chat_id == chat_id,
            User.active.is_(True),
            Branch.active.is_(True),
        )
        .first()
    )

    if resultado is None:
        return None

    return IdentidadTelegram(
        usuario_id=resultado[0],
        sucursal_id=resultado[1],
    )
