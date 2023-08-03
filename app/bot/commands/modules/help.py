from app.bot.api import Api
from app.bot.commands import Command, CommandRegistry


class HelpCommand(Command):
    """Выводит список всех команд или помощь по команде"""

    name = "help"

    aliases = ["commands", "команды"]

    usage = "!help [имя команды]"
    example = "!help | !help отчикрыжить"

    async def handle(self, parts, message, db):
        await super().handle(parts, message, db)

        args = parts[1:]

        commands = {
            k: v
            for k, v in CommandRegistry.get_commands().items()
            if v.has_perms(message)
        }

        response = f"Команды: {', '.join(sorted(list(commands.keys())))}"
        if len(args) != 0:
            if command := commands.get(args[0].lower()):
                response = command.get_help()

        api = Api()
        await api.send(response, message.channel_id)
