from abc import abstractmethod

from sqlalchemy.orm import Session

from .registry import CommandRegistry
from ...api.trovo.schemas import Message


class CommandInterface(metaclass=CommandRegistry):
    name: str
    aliases: list[str]

    disabled = False

    @abstractmethod
    async def handle(self, parts: list[str], message: Message, db: Session):
        ...
