from app.bot.commands import as_command, CommandBase
from .utils import get_rank_message


@as_command
class TopCommand(CommandBase):
    """Вывести информацию о текущем топе часа"""

    name = "топ"

    usage = "!топ"

    @classmethod
    async def handle(cls, parts, message, db):
        await super().handle(parts, message, db)

        msg = await get_rank_message(cls.api.network.channel_id)

        await cls.api.send(
            msg,
            cls.api.network.channel_id,
        )