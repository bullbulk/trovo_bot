from app.bot.api import Api
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

        api = Api()
        msg = await get_rank_message(message.channel_id)

        await api.send(
            msg,
            message.channel_id,
        )
