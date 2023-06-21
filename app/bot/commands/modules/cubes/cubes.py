from app import crud
from app.bot.api import Api
from app.bot.commands import Command
from app.bot.utils import calc_dices_result


class CubeCommand(Command):
    """Списать кубы со счёта и замьютить пользоватея на выпавшее количество десятков минут"""

    name = "отпежить"

    usage = "!отпежить <@никнейм> [количество]"
    example = "!отпежить @bullbulk 10 | !отпежить @bullbulk (кинет 1 куб) "

    @classmethod
    async def handle(cls, parts, message, db):
        await super().handle(parts, message, db)

        api = Api()

        try:
            target = parts[1]
            target = target.removeprefix("@")
            if target.lower() in ["fedorbot2", "fedorbot"]:
                await api.send(
                    f"@{message.nick_name} анус свой отпежь, пёс",
                    message.channel_id,
                )
                return

            amount = 1
            if len(parts) >= 3:
                if parts[2].isnumeric():
                    amount = int(parts[2])
                if amount <= 0:
                    amount = 1

        except IndexError:
            await api.send(f"Использование: {cls.usage}", message.channel_id)
            return

        dice_amount = crud.dice_amount.get_by_owner(db, user_id=message.sender_id)

        dice_amount_num = getattr(dice_amount, "amount", 0)
        if dice_amount_num < amount:
            await api.send(
                f"@{message.nick_name} у тебя недостаточно кубов",
                message.channel_id,
            )
            return

        dices_results = await calc_dices_result(amount)

        success_dices_num = sum(y for x, y in dices_results.items() if x > 3)
        result_str = ", ".join(
            [
                f"{x} ({y} шт.)"
                for x, y in sorted(dices_results.items(), key=lambda v: v[0])
            ]
        )

        subtract_cubes = False

        if not success_dices_num:
            await api.send(
                f"@{message.nick_name} результат: {result_str}, {target} выживает",
                message.channel_id,
            )
            subtract_cubes = True
        else:
            ban_seconds = success_dices_num * 600

            data = await api.command(f"ban {target} {ban_seconds}", message.channel_id)
            data = await data.json()

            if data.get("is_success"):
                await api.send(
                    f"@{message.nick_name} результат: {result_str}, "
                    f"{target} отлетает на {ban_seconds // 60} минут",
                    message.channel_id,
                )
                subtract_cubes = True
            else:
                await api.send(
                    f"@{message.nick_name} результат: {result_str}, "
                    f"{target} должен был отлететь на {ban_seconds // 60} минут, "
                    f"но при мьюте произошла ошибка. "
                    f"Возможно, ты неправильно написал ник или пользователь уже в бане",
                    message.channel_id,
                )

        if subtract_cubes:
            crud.dice_amount.subtract(db, db_obj=dice_amount, amount=amount)
