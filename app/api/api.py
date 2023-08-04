from fastapi import APIRouter

from .endpoints import login, users, bot, items

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(bot.router, prefix="/bot", tags=["bot"])
api_router.include_router(items.router, prefix="/tracks", tags=["bot"])
