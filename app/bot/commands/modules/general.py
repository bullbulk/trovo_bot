from app.bot.commands import as_command, CommandBase


@as_command
class HosepCommand(CommandBase):
    name = "хосе"
    disabled = True

    @classmethod
    async def handle(cls, parts, message, db):
        await super().handle(parts, message, db)

        message = "ниоч"

        if parts[0].isupper():
            message = message.upper()

        await cls.api.send(message, cls.api.network.channel_id)


@as_command
class InvokeCommand(CommandBase):
    """Выполнить команду от имени бота. Доступно только пользователям с ролью "модератор" и выше"""

    name = "invoke"
    moderator_only = True

    usage = "!invoke <имя команды> [*аргументы]"
    example = "!invoke ban bullbulk 30"

    @classmethod
    async def handle(cls, parts: list[str], message, db):
        await super().handle(parts, message, db)

        args = parts[1:]

        result = await cls.api.command(
            command=" ".join(args), channel_id=cls.api.network.channel_id
        )
        data = await result.json()
        await cls.api.send(data["display_msg"], cls.api.network.channel_id)
