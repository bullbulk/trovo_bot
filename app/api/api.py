from fastapi import APIRouter

from .endpoints import login, users, bot

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(bot.router, prefix="/bot", tags=["bot"])
