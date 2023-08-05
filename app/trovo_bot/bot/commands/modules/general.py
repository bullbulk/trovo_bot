from app.trovo_bot.bot.trovo import TrovoApi
from app.trovo_bot.bot.commands import Command


class HosepCommand(Command):
    name = "хосе"
    disabled = True

    async def handle(self, parts, message, db):
        await super().handle(parts, message, db)

        api = TrovoApi()
        response = "ниоч"

        if parts[0].isupper():
            response = response.upper()

        await api.send(response, message.channel_id)


class InvokeCommand(Command):
    """Выполнить команду от имени бота. Доступно только пользователям с ролью "модератор" и выше"""

    name = "invoke"
    moderator_only = True

    usage = "!invoke <имя команды> [*аргументы]"
    example = "!invoke ban bullbulk 30"

    async def handle(self, parts: list[str], message, db):
        await super().handle(parts, message, db)

        api = TrovoApi()
        args = parts[1:]

        result = await api.command(
            command=" ".join(args), channel_id=message.channel_id
        )
        data = await result.json()
        await api.send(data["display_msg"], message.channel_id)
