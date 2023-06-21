from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.bot.api.schemas import Message


class CommandInterface(ABC):
    name: str

    @abstractmethod
    async def handle(self, parts: list[str], message: Message, db: Session):
        ...
