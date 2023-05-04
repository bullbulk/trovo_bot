from typing import TypeVar

from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.bot.api import Api
from app.bot.api.schemas import Message
from app.config import settings
from .interface import CommandInterface
from ...exceptions import CommandDisabled


class CommandBase(CommandInterface):
    disabled = False
    owner_only = False
    moderator_only = False

    usage = ""
    example = ""

    @classmethod
    async def handle(cls, parts: list[str], message: Message, db: Session):
        if cls.disabled:
            raise CommandDisabled

    @classmethod
    async def process(cls, parts: list[str], message: Message):
        is_owner = message.sender_id == settings.TROVO_OWNER_ID
        if cls.owner_only and not is_owner:
            return
        if (
            cls.moderator_only
            and not is_owner
            and "mod" not in message.roles
            and "streamer" not in message.roles
        ):
            return
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

    @classmethod
    def get_help(cls):
        text = f"Команда !{cls.name} @@ {cls.__doc__}"
        if cls.usage:
            text += f" @@ Использование: {cls.usage} @@ (<> - обязательный, [] - необязательный аргумент)"
        if cls.example:
            text += f" @@ Пример использования: {cls.example}"
        return text


CommandInstance = TypeVar("CommandInstance", bound=CommandBase)
