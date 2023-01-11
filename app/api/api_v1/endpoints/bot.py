from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.bot import bot_instance
from app.core.config import set_config

router = APIRouter()


@router.get("/login", response_model=schemas.OAuthUri)
def login(
        db: Session = Depends(deps.get_db),
        # current_superuser: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get OAuth URI to login as bot user.
    """

    return {"uri": bot_instance.api.network.generate_oauth_uri()}


@router.get('/oauth')
async def oauth(
        code: str,
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get exchange code for Trovo OAuth.
    """

    await bot_instance.api.network.exchange(code)
    return {"result": "success", "code": code}


@router.get('/set_nickname')
async def oauth(
        nickname: str,
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get exchange code for Trovo OAuth.
    """

    set_config(db, "trovo_channel_nickname", nickname)
    await bot_instance.api.chat.connect()
    return {"result": "success", "trovo_channel_nickname": nickname}


@router.get('/refresh')
async def oauth(
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get exchange code for Trovo OAuth.
    """

    await bot_instance.api.network.refresh()
    return {"a": "d"}
