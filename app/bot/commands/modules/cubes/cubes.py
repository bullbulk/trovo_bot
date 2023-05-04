from random import randint

from app import crud
from app.bot.commands import as_command, CommandBase


@as_command
class CubeCommand(CommandBase):
    """Списать кубы со счёта и замьютить пользоватея на выпавшее количество десятков минут"""

    name = "отпежить"

    usage = "!отпежить <@никнейм> [количество]"
    example = "!отпежить @bullbulk 10 | !отпежить @bullbulk (кинет 1 куб) "

    @classmethod
    async def handle(cls, parts, message, db):
        await super().handle(parts, message, db)

        try:
            target = parts[1]
            target = target.removeprefix("@")
            if target.lower() in ["fedorbot2", "fedorbot"]:
                await cls.api.send(
                    f"@{message.nick_name} анус свой отпежь, пёс",
                    cls.api.network.channel_id,
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
                f"Использование: {cls.usage}", cls.api.network.channel_id
            )
            return

        dice_amount = crud.dice_amount.get_by_owner(db, user_id=message.sender_id)

        dice_amount_num = getattr(dice_amount, "amount", 0)
        if dice_amount_num < amount:
            await cls.api.send(
                f"@{message.nick_name} у тебя недостаточно кубов",
                cls.api.network.channel_id,
            )
            return

        dices_results = calc_dices_result(amount)

        success_dices_num = sum(y for x, y in dices_results.items() if x > 3)
        result_str = ", ".join(
            [
                f"{x} ({y} шт.)"
                for x, y in sorted(dices_results.items(), key=lambda v: v[0])
            ]
        )

        subtract_cubes = False

        if not success_dices_num:
            await cls.api.send(
                f"@{message.nick_name} результат: {result_str}, {target} выживает",
                cls.api.network.channel_id,
            )
            subtract_cubes = True
        else:
            ban_seconds = success_dices_num * 600

            data = await cls.api.command(
                f"ban {target} {ban_seconds}", cls.api.network.channel_id
            )
            data = await data.json()

            if data.get("is_success"):
                await cls.api.send(
                    f"@{message.nick_name} результат: {result_str}, "
                    f"{target} отлетает на {ban_seconds // 60} минут",
                    cls.api.network.channel_id,
                )
                subtract_cubes = True
            else:
                await cls.api.send(
                    f"@{message.nick_name} результат: {result_str}, "
                    f"{target} должен был отлететь на {ban_seconds // 60} минут, "
                    f"но при мьюте произошла ошибка. "
                    f"Возможно, ты неправильно написал ник или пользователь уже в бане",
                    cls.api.network.channel_id,
                )

        if subtract_cubes:
            crud.dice_amount.subtract(db, db_obj=dice_amount, amount=amount)


def calc_dices_result(amount: int) -> dict[int, int]:
    dices_result = {}

    for _ in range(amount):
        result = randint(1, 6)
        if dices_result.get(result):
            dices_result[result] += 1
        else:
            dices_result[result] = 1

    return dices_result
