from sqlalchemy import Column, Integer

from app.db.base_class import Base


class DiceAmount(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    amount = Column(Integer)
