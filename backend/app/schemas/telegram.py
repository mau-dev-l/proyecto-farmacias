from datetime import datetime

from pydantic import BaseModel


class LinkCodeResponse(BaseModel):
    codigo: str
    expira_en: datetime


class LinkStatusResponse(BaseModel):
    vinculado: bool
    vinculado_en: datetime | None = None
    bot_username: str | None = None
