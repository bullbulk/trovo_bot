from app.trovo_bot.bot.api import TrovoApi
from app.trovo_bot.bot.commands import Command
from .utils import get_rank_message


class TopCommand(Command):
    """Вывести информацию о текущем топе часа"""

    name = "топ"
    aliases = ["top", "t"]

    usage = "!топ"

    async def handle(self, parts, message, db):
        await super().handle(parts, message, db)

        api = TrovoApi()
        msg = await get_rank_message(message.channel_id)

        await api.send(
            msg,
            message.channel_id,
        )
