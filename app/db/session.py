from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.utils.config import settings

engine = create_engine(settings.DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
