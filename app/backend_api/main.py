from fastapi import FastAPI

from app.backend_api.api import api_router
from app.utils import logger
from app.utils.api import setup_middleware
from app.utils.config import settings

logger.init()

app = FastAPI(title=settings.PROJECT_NAME, openapi_url="/openapi.json")

setup_middleware(app)

app.include_router(api_router)

