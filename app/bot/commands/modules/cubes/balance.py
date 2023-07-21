from app import crud
from app.bot.api import Api
from app.bot.commands import Command


class BalanceCommand(Command):
    """Получить количество кубов на балансе. Кубы можно получить за отправку спелла MrCube"""

    name = "баланс"

    usage = "!баланс [@никнейм]"
    example = "!баланс @bullbulk | !баланс (получить свой баланс)"

    async def handle(self, parts, message, db):
        await super().handle(parts, message, db)

        api = Api()

        target_id = None
        target = None

        if len(parts) > 1:
            target = parts[1].removeprefix("@")
            if target not in ["fedorbot", "fedorbot2"]:
                res = await api.get_channel_info(username=target)
                channel_info = await res.json()

                res = await api.get_users([channel_info.get("username")])
                users_data = await res.json()

                users = users_data.get("users", [{}])
                target_id = users[0].get("channel_id")

        if not target_id:
            target_id = message.sender_id

        dice_amount = crud.dice_amount.get_by_owner(db, user_id=target_id)
        result_amount = getattr(dice_amount, "amount", 0)

        if target_id == message.sender_id:
            response_message = (
                f"@{message.nick_name} кубов у тебя на счету: {result_amount}"
            )
        else:
            response_message = (
                f"@{message.nick_name} кубов на счету у {target}: {result_amount}"
            )

        await api.send(response_message, message.channel_id)
