from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/telegram", tags=["telegram"])
bot_router = APIRouter(prefix="/bot", tags=["telegram"])


@router.post("/codigo")
def create_link_code() -> None:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Telegram integration is deferred")


@router.post("/vincular")
def link_chat() -> None:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Telegram integration is deferred")


@bot_router.post("/consulta")
def bot_query() -> None:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="LLM integration is deferred")
