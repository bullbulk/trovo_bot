from sqlalchemy.orm import Session

from app import crud
from app import schemas
from app.bot.api.schemas import Message
from app.bot.commands import as_command, CommandBase
from app.bot.exceptions import IncorrectUsage
from app.bot.utils import calc_dices_result
from .controllers.massban import MassBanController


@as_command
class MassCubeCommand(CommandBase):
    """
    Списать кубы со счёта и замьютить следующих выпавшее N-количество участников
    чата по роли и/или тексту-триггеру на 10 минут
    """

    name = "отчикрыжить"

    usage = "!отчикрыжить <@название_роли или * (все участники)> <количество> [триггер текст]"
    example = "!отчикрыжить @трипек 10 хочу бан | !отчикрыжить * 10 ПЕК ПЕК ПЕК"

    @classmethod
    async def handle(cls, parts: list[str], message: Message, db: Session):
        await super().handle(parts, message, db)

        args = parts[1:]

        try:
            if len(args) < 2:
                raise IncorrectUsage

            target_role, amount, *trigger_text = args
            target_role = target_role.removeprefix("@")
            trigger_text = " ".join(trigger_text).lower()

            if target_role.lower() in ["streamer", "mod", "supermod"]:
                await cls.api.send(
                    f"@{message.nick_name} анус свой отпежь, пёс",
                    cls.api.network.channel_id,
                )
                return
            elif target_role == "*":
                target_role = None

            if amount.isnumeric():
                amount = int(amount)
            else:
                raise IncorrectUsage

        except IncorrectUsage:
            await cls.api.send(
                f"Использование: {cls.usage}",
                cls.api.network.channel_id,
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

        dices_results = await calc_dices_result(amount)

        success_dices_num = sum(y for x, y in dices_results.items() if x > 3)
        result_str = ", ".join(
            [
                f"{x} ({y} шт.)"
                for x, y in sorted(dices_results.items(), key=lambda v: v[0])
            ]
        )

        if target_role:
            target_members_text = f'участников чата с ролью "{target_role}"'
        else:
            target_members_text = "всех участников чата"

        if not success_dices_num:
            await cls.api.send(
                f"@{message.nick_name} решил отчикрыжить {target_members_text} @@ "
                f"Увы, результат: {result_str} @@ "
                f"Всего: {success_dices_num}",
                cls.api.network.channel_id,
            )
        else:
            begin_message = (
                f"\n@{message.nick_name} решил отчикрыжить {target_members_text} @@ "
                f"Результат: {result_str} @@ "
                f"Всего: {success_dices_num} @@ "
            )
            if trigger_text:
                begin_message += f'Триггер: "{trigger_text}" @@ '
            begin_message += "Да начнётся жатва!"

            await cls.api.send(
                begin_message,
                cls.api.network.channel_id,
            )

            crud.mass_dice_entry.create(
                db,
                obj_in=schemas.MassDiceEntry(
                    issuer_id=message.sender_id,
                    issuer_nickname=message.nick_name,
                    amount=success_dices_num,
                    trigger_text=trigger_text,
                    target_role=target_role,
                ),
            )
            MassBanController.update_active_entries(db)

        crud.dice_amount.subtract(db, db_obj=dice_amount, amount=amount)
