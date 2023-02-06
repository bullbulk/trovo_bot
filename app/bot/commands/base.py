from abc import ABC

from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.bot.api import Api
from app.bot.api.schemas import Message


class abstractclassmethod(classmethod):  # noqa
    __isabstractmethod__ = True

    def __init__(self, _callable):
        _callable.__isabstractmethod__ = True
        super(abstractclassmethod, self).__init__(_callable)


class CommandInterface(ABC):
    name: str
    api: Api

    @abstractclassmethod
    async def handle(cls, parts: list[str], message: Message, db: Session):
        pass

    @classmethod
    async def process(cls, parts: list[str], message: Message):
        db = cls.get_db()
        try:
            await cls.handle(parts=parts, message=message, db=db)
        finally:
            db.close()

    @classmethod
    def set_api(cls, api: Api):
        cls.api = api

    @staticmethod
    def get_db():
        return next(get_db())
