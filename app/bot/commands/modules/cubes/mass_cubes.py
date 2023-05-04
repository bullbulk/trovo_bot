import asyncio
from random import randint

from sqlalchemy import insert
from sqlalchemy.orm import Session

from app import crud
from app import schemas
from app.bot.api.schemas import Message
from app.bot.commands import as_command, CommandBase
from app.bot.exceptions import IncorrectUsage
from app.models import MassDiceEntry, MassDiceBanRecord


@as_command
class MassCubeCommand(CommandBase):
    """
    Списать кубы со счёта и замьютить следующих выпавшее N-количество участников
    чата по роли и/или тексту-триггеру на 10 минут
    """

    name = "отчикрыжить"

    usage = "!отчикрыжить <@название_роли или * (все участники)> <количество> [триггер текст]"
    example = "!отчикрыжить @трипек 10 хочу бан | !отчикрыжить * 10 ПЕК ПЕК ПЕК"

    active_entries: dict[str, list[schemas.MassDiceEntry]] | None = None

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
            if target_role == "*":
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

        dices_results = calc_dices_result(amount)

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
            cls.update_active_entries(db)

        crud.dice_amount.subtract(db, db_obj=dice_amount, amount=amount)

    @classmethod
    def update_active_entries(cls, db: Session):
        entries = crud.mass_dice_entry.get_active_multi(db)
        grouped_entries = {}

        for entry in entries:
            role = entry.target_role
            if role not in grouped_entries:
                grouped_entries[role] = []
            grouped_entries[role].append(entry)

        cls.active_entries = grouped_entries

    @classmethod
    async def handle_message(cls, message: Message, db: Session):
        # sourcery skip: for-append-to-extend
        if cls.active_entries is None:
            cls.update_active_entries(db)

        applied_entries = []
        for role, entries in cls.active_entries.items():
            if role and role not in message.roles:
                continue

            for entry in entries:
                if (
                    not entry.trigger_text
                    or entry.trigger_text in message.content.lower()
                ):
                    applied_entries.append(entry)

        if not applied_entries:
            return

        ban_seconds = len(applied_entries) * 600

        target = message.nick_name
        data = await cls.api.command(
            f"ban {target} {ban_seconds}", cls.api.network.channel_id
        )
        data = await data.json()

        ban_success = data.get("is_success", False)

        if not ban_success:
            return

        ban_records = []
        for entry in applied_entries:
            entry = crud.mass_dice_entry.subtract(
                db, db_obj=entry, amount=entry.amount - 1
            )
            cls.update_active_entries(db)
            if entry.amount <= 0:
                asyncio.create_task(cls.finish_mass_entry(entry))
            ban_records.append(
                dict(
                    user_id=message.sender_id,
                    user_nickname=message.nick_name,
                    entry_id=entry.id,
                )
            )

        if ban_records:
            db.execute(insert(MassDiceBanRecord), ban_records)

    @classmethod
    async def finish_mass_entry(cls, entry: MassDiceEntry):
        banned_nicknames = list(
            set(map(lambda x: f"@{x.user_nickname}", entry.records))
        )

        target_role_text = (
            f' на роль "{entry.target_role}"' if entry.target_role else ""
        )
        await cls.api.send(
            f"Отчикрыживание от @{entry.issuer_nickname}{target_role_text} окончено! @@ "
            f"Потерпевшие ({len(banned_nicknames)}): {' '.join(banned_nicknames)}",
            cls.api.network.channel_id,
        )


def calc_dices_result(amount: int) -> dict[int, int]:
    dices_result = {}

    for _ in range(amount):
        result = randint(1, 6)
        if dices_result.get(result):
            dices_result[result] += 1
        else:
            dices_result[result] = 1

    return dices_result
