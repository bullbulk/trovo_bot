from app.bot.commands import as_command, get_commands, CommandBase


@as_command
class HelpCommand(CommandBase):
    name = "help"

    @classmethod
    async def handle(cls, parts, message, db):
        await super().handle(parts, message, db)

        response = f"Команды: {', '.join(sorted(list(get_commands().keys())))}"

        await cls.api.send(response, cls.api.network.channel_id)
