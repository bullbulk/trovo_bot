from abc import ABC

from sqlalchemy.orm import Session

from app.bot.api.schemas import Message


class abstractclassmethod(classmethod):  # noqa
    __isabstractmethod__ = True

    def __init__(self, _callable):
        _callable.__isabstractmethod__ = True
        super(abstractclassmethod, self).__init__(_callable)


class CommandInterface(ABC):
    name: str

    @abstractclassmethod
    async def handle(cls, parts: list[str], message: Message, db: Session):
        pass
