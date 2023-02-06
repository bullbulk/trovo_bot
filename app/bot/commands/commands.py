from random import randint

from app.bot.commands.base import CommandInterface
from app.bot.commands.list_mixin import command_list, CommandListMixin
from app.models import DiceAmount


@command_list
class CubeCommand(CommandInterface):
    name = "отпежить"

    @classmethod
    async def handle(cls, parts, message, db):
        try:
            target = parts[1]
            target = target.removeprefix("@")
            if target.lower() in ["fedorbot2", "fedorbot"]:
                await cls.api.send(
                    f"@{message.nick_name} анус свой отпежь, пёс",
                    cls.api.network.channel_id
                )
                return

            amount = 1
            if len(parts) >= 3:
                if parts[2].isnumeric():
                    amount = int(parts[2])
                if amount <= 0:
                    amount = 1

        except IndexError:
            await cls.api.send(
                "Использование: !отпежить <никнейм>",
                cls.api.network.channel_id
            )
            return

        dice_amount = db.query(DiceAmount).filter(DiceAmount.user_id == message.sender_id).first()

        if dice_amount:
            dice_amount_num = dice_amount.amount
        else:
            dice_amount_num = 0

        if dice_amount_num < amount:
            await cls.api.send(
                f"@{message.nick_name} у тебя недостаточно кубов",
                cls.api.network.channel_id
            )
            return

        dices_results = {}

        for i in range(amount):
            result = randint(1, 6)
            if dices_results.get(result):
                dices_results[result] += 1
            else:
                dices_results[result] = 1

        success_dices_num = sum([y for x, y in dices_results.items() if x > 3])
        result_str = ", ".join(
            [f"{x} ({y} шт.)" for x, y in sorted(
                dices_results.items(), key=lambda v: v[0]
            )]
        )

        subtract_cubes = False

        if not success_dices_num:
            await cls.api.send(
                f"@{message.nick_name} результат: {result_str}, {target} выживает",
                cls.api.network.channel_id
            )
            subtract_cubes = True
        else:
            ban_seconds = success_dices_num * 600

            data = await cls.api.command(
                f"ban {target} {ban_seconds}",
                cls.api.network.channel_id
            )
            data = await data.json()

            if data.get("is_success"):
                await cls.api.send(
                    f"@{message.nick_name} результат: {result_str}, "
                    f"{target} отлетает на {ban_seconds // 60} минут",
                    cls.api.network.channel_id
                )
                subtract_cubes = True
            else:
                await cls.api.send(
                    f"@{message.nick_name} результат: {result_str}, "
                    f"{target} должен был отлететь на {ban_seconds // 60} минут, "
                    f"но при мьюте произошла ошибка. "
                    f"Возможно, ты неправильно написал ник или пользователь уже в бане",
                    cls.api.network.channel_id
                )

        if subtract_cubes:
            dice_amount.amount -= amount
            db.add(dice_amount)
            db.commit()
            db.refresh(dice_amount)


@command_list
class HelpCommand(CommandInterface):
    name = "help"

    @classmethod
    async def handle(cls, parts, message, db):
        response = f"Команды: {', '.join(sorted(list(CommandListMixin.commands.keys())))}"

        await cls.api.send(
            response,
            cls.api.network.channel_id
        )


@command_list
class BalanceCommand(CommandInterface):
    name = "баланс"

    @classmethod
    async def handle(cls, parts, message, db):
        target_id = None
        target = None

        if len(parts) > 1:
            target = parts[1].removeprefix("@")
            if target not in ["fedorbot", "fedorbot2"]:
                request = await cls.api.get_users([target])
                data = await request.json()

                users = data.get("users", [{}])
                target_id = users[0].get("channel_id")

        if not target_id:
            target_id = message.sender_id

        dice_amount = db.query(DiceAmount).filter(DiceAmount.user_id == target_id).first()
        if dice_amount:
            result_amount = dice_amount.amount
        else:
            result_amount = 0

        if target_id == message.sender_id:
            response_message = f"@{message.nick_name} кубов у тебя на счету: {result_amount}"
        else:
            response_message = f"@{message.nick_name} кубов на счету у {target}: {result_amount}"

        await cls.api.send(
            response_message,
            cls.api.network.channel_id
        )
