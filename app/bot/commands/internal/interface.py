from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.bot.api.schemas import Message
from .registry import CommandRegistry


class CommandInterface(metaclass=CommandRegistry):
    name: str
    aliases: list[str]

    disabled = False

    @abstractmethod
    async def handle(self, parts: list[str], message: Message, db: Session):
        ...
