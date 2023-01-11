import asyncio

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app import import logger
from app.api.api_v1.api import api_router
from app.api.deps import get_db
from app.bot import bot_instance
from app.config import settings
from core.config import set_config

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

logger.init()
set_config(next(get_db()), "refresh_token", "7e93096363d049cb9b590ef9e116f0bd")


@app.on_event("startup")
async def on_startup():
    loop = asyncio.get_running_loop()
    loop.create_task(bot_instance.run())
