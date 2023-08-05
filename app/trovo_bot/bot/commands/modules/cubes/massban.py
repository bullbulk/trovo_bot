from sqlalchemy.orm import Session

from app.trovo_bot.bot.api import TrovoApi
from app.trovo_bot.bot.api.trovo.schemas import Message
from app.trovo_bot.bot.commands import Command
from app.trovo_bot.bot.exceptions import IncorrectUsage
from app.trovo_bot.bot.utils import create_massban_entry


class MassBanCommand(Command):
    """
    Списать кубы со счёта и замьютить следующих выпавшее N-количество участников
    чата по роли и/или тексту-триггеру на 10 минут
    """

    name = "massban"

    usage = (
        "!massban <@название_роли или * (все участники)> <количество> [триггер текст]"
    )
    example = "!massban @двупек 10 ПЕК ПЕК | !massban * 10 хочу бан"

    streamer_only = True

    async def handle(self, parts: list[str], message: Message, db: Session):
        await super().handle(parts, message, db)

        api = TrovoApi()
        args = parts[1:]

        if len(args) < 2:
            raise IncorrectUsage

        target_role, amount, *trigger_text = args
        target_role = target_role.removeprefix("@").lower()
        trigger_text = " ".join(trigger_text).lower()

        if target_role in ["streamer", "mod", "supermod"]:
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

        create_massban_entry(
            db=db,
            message=message,
            amount=amount,
            trigger_text=trigger_text,
            target_role=target_role,
        )
