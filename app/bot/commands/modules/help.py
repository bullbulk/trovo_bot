from app.bot.commands import as_command, get_commands, CommandBase


@as_command
class HelpCommand(CommandBase):
    """Выводит список всех команд или помощь по команде"""

    name = "help"

    usage = "!help [имя команды]"
    example = "!help | !help отчикрыжить"

    @classmethod
    async def handle(cls, parts, message, db):
        await super().handle(parts, message, db)

        args = parts[1:]

        response = f"Команды: {', '.join(sorted(list(get_commands().keys())))}"
        if len(args) != 0:
            if command := get_commands().get(args[0].lower()):
                response = command.get_help()

        await cls.api.send(response, cls.api.network.channel_id)