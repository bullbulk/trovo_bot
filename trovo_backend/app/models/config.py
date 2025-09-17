from sqlalchemy import Column, Integer, String

from app.db.base_class import Base


class Config(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    value = Column(String)
