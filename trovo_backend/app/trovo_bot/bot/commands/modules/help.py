from app.trovo_bot.bot.trovo import TrovoApi
from app.trovo_bot.bot.commands import Command, CommandRegistry


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

        unique_commands = set(commands.values())

        commands_prompts = []
        for command in list(unique_commands):
            s = f"{command.name}"
            if command.aliases:
                s += f" ({', '.join(command.aliases)})"
            commands_prompts.append(s)

        response = f"Команды: {', '.join(sorted(list(commands_prompts)))}"
        if len(args) != 0:
            if command := commands.get(args[0].lower()):
                response = command.get_help()

        api = TrovoApi()
        await api.send(response, message.channel_id)
