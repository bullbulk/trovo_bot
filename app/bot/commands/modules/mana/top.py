from app.bot.api import Api
from app.bot.commands import Command
from .utils import get_rank_message


class TopCommand(Command):
    """Вывести информацию о текущем топе часа"""

    name = "топ"
    aliases = ["top", "t"]

    usage = "!топ"

    @classmethod
    async def handle(cls, parts, message, db):
        await super().handle(parts, message, db)

        api = Api()
        msg = await get_rank_message(message.channel_id)

        await api.send(
            msg,
            message.channel_id,
        )
