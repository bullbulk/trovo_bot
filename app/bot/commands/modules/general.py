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
