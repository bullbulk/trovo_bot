from typing import TypeVar

from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.bot.api.schemas import Message
from app.config import settings
from .interface import CommandInterface
from .singleton import SingletonRegistry


class CommandBase(CommandInterface, SingletonRegistry):
    name: str

    disabled = False
    owner_only = False
    moderator_only = False
    streamer_only = False

    usage = ""
    example = ""

    @classmethod
    async def handle(cls, parts: list[str], message: Message, db: Session):
        pass

    @classmethod
    async def process(cls, parts: list[str], message: Message):
        if not cls.has_perms(message):
            return
        db = cls.get_db()
        try:
            await cls.handle(parts=parts, message=message, db=db)
        finally:
            db.close()

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

    @classmethod
    def has_perms(cls, message: Message):
        if cls.disabled:
            return False

        is_owner = message.sender_id == settings.TROVO_OWNER_ID

        if is_owner:
            return True

        if not any([cls.moderator_only, cls.streamer_only, cls.owner_only]):
            return True

        if cls.moderator_only and (
            "mod" in message.roles or "streamer" in message.roles
        ):
            return True

        if cls.streamer_only and "streamer" in message.roles:
            return True


CommandInstance = TypeVar("CommandInstance", bound=CommandBase)
