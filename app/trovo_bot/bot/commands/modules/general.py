from app.trovo_bot.bot.commands import Command
from app.trovo_bot.bot.exceptions import IncorrectUsage
from app.trovo_bot.bot.trovo import TrovoApi


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


class AddroleCommand(Command):
    """Добавить роль пользователям. Доступно только пользователям с ролью "модератор" и выше"""

    name = "addrole"
    moderator_only = True

    usage = "!addrole <Роль> [*никнеймы]"
    example = "!addrole Чемпион bullbulk G1deonTV"

    async def handle(self, parts: list[str], message, db):
        await super().handle(parts, message, db)

        api = TrovoApi()
        role = parts[1]
        nicknames = parts[2:]

        for nickname in nicknames:
            nickname = nickname.removeprefix("@")
            result = await api.command(
                command=f"addrole {role} {nickname}", channel_id=message.channel_id
            )
            data = await result.json()
            await api.send(data["display_msg"], message.channel_id)


class RemoveroleCommand(Command):
    """Удалить роль у пользователей. Доступно только пользователям с ролью "модератор" и выше"""

    name = "removerole"
    moderator_only = True

    usage = "!removerole <Роль> [*никнеймы]"
    example = "!removerole Чемпион bullbulk G1deonTV"

    async def handle(self, parts: list[str], message, db):
        await super().handle(parts, message, db)

        args = parts[1:]

        if len(args) < 2:
            raise IncorrectUsage

        api = TrovoApi()
        role = args[0]
        nicknames = args[1:]

        for nickname in nicknames:
            nickname = nickname.removeprefix("@")
            result = await api.command(
                command=f"removerole {role} {nickname}", channel_id=message.channel_id
            )
            data = await result.json()
            await api.send(data["display_msg"], message.channel_id)
