from typing import Any

from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import as_declarative, declared_attr

from app.utils.config import settings


@as_declarative()
class Base:
    __name__: str
    __abstract__ = True

    id: Any
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    @classmethod
    @declared_attr
    def __tablename__(cls) -> str:
        name = cls.__name__.lower() or cls.__tablename__
        if settings.DB_PREFIX:
            return f"{settings.DB_PREFIX}_{name}"
        return name
