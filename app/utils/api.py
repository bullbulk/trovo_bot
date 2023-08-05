from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.utils.config import settings


def setup_middleware(app: FastAPI):
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
