from typing import TypeVar

from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.bot.api import Api
from app.bot.api.schemas import Message
from .interface import CommandInterface
from ...errors import CommandDisabled


class CommandBase(CommandInterface):
    disabled = False

    @classmethod
    async def handle(cls, parts: list[str], message: Message, db: Session):
        if cls.disabled:
            raise CommandDisabled

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


CommandInstance = TypeVar("CommandInstance", bound=CommandBase)
