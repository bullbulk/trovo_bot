from typing import TypeVar

from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.bot.api.schemas import Message
from app.config import settings
from .interface import CommandInterface
from .registry import CommandRegistry


class Command(CommandInterface, metaclass=CommandRegistry):
    name: str
    aliases: list[str]

    disabled = False
    owner_only = False
    moderator_only = False
    streamer_only = False

    usage = ""
    example = ""

    async def handle(self, parts: list[str], message: Message, db: Session):
        pass

    async def process(self, parts: list[str], message: Message):
        if not self.has_perms(message):
            return
        db = self.get_db()
        try:
            await self.handle(parts=parts, message=message, db=db)
        finally:
            db.close()

    @staticmethod
    def get_db():
        return next(get_db())

    def get_help(self):
        text = f"Команда !{self.name} @@ {self.__doc__}"
        if self.usage:
            text += f" @@ Использование: {self.usage} @@ (<> - обязательный, [] - необязательный аргумент)"
        if self.example:
            text += f" @@ Пример использования: {self.example}"
        return text

    def has_perms(self, message: Message):
        if self.disabled:
            return False

        is_owner = message.sender_id == settings.TROVO_OWNER_ID

        if is_owner:
            return True

        if not any([self.moderator_only, self.streamer_only, self.owner_only]):
            return True

        if self.moderator_only and (
            "mod" in message.roles or "streamer" in message.roles
        ):
            return True

        if self.streamer_only and "streamer" in message.roles:
            return True


CommandInstance = TypeVar("CommandInstance", bound=Command)
