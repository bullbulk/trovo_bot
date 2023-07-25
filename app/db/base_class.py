from typing import Any

from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    __name__: str
    __abstract__ = True

    id: Any
    created_at = Column(DateTime, server_default=func.now())

    @classmethod
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
