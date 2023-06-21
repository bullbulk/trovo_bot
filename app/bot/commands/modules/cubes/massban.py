from sqlalchemy.orm import Session

from app import crud
from app import schemas
from app.bot.api import Api
from app.bot.api.schemas import Message
from app.bot.commands import as_command, CommandBase
from app.bot.exceptions import IncorrectUsage
from .controllers.massban import MassBanController


@as_command
class MassBanCommand(CommandBase):
    """
    Списать кубы со счёта и замьютить следующих выпавшее N-количество участников
    чата по роли и/или тексту-триггеру на 10 минут
    """

    name = "massban"

    usage = (
        "!massban <@название_роли или * (все участники)> <количество> [триггер текст]"
    )
    example = "!massban @трипек 10 хочу бан | !отчикрыжить * 10 ПЕК ПЕК ПЕК"

    streamer_only = True

    @classmethod
    async def handle(cls, parts: list[str], message: Message, db: Session):
        await super().handle(parts, message, db)

        api = Api()
        args = parts[1:]

        try:
            if len(args) < 2:
                raise IncorrectUsage

            target_role, amount, *trigger_text = args
            target_role = target_role.removeprefix("@")
            trigger_text = " ".join(trigger_text).lower()

            if target_role.lower() in ["streamer", "mod", "supermod"]:
                await api.send(
                    f"@{message.nick_name} анус свой отпежь, пёс",
                    message.channel_id,
                )
                return
            elif target_role == "*":
                target_role = None

            if amount.isnumeric():
                amount = int(amount)
            else:
                raise IncorrectUsage

        except IncorrectUsage:
            await api.send(
                f"Использование: {cls.usage}",
                message.channel_id,
            )
            return

        if target_role:
            target_members_text = f'участников чата с ролью "{target_role}"'
        else:
            target_members_text = "всех участников чата"

        begin_message = (
            f"\n@{message.nick_name} решил отчикрыжить {target_members_text} @@ "
            f"Всего: {amount} @@ "
        )
        if trigger_text:
            begin_message += f'Триггер: "{trigger_text}" @@ '
        begin_message += "Да начнётся жатва!"

        await api.send(
            begin_message,
            message.channel_id,
        )

        crud.mass_dice_entry.create(
            db,
            obj_in=schemas.MassDiceEntry(
                issuer_id=message.sender_id,
                issuer_nickname=message.nick_name,
                amount=amount,
                trigger_text=trigger_text,
                target_role=target_role,
            ),
        )
        MassBanController.update_active_entries(db)
