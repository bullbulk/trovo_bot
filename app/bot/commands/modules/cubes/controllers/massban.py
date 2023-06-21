import asyncio

from sqlalchemy import insert
from sqlalchemy.orm import Session

from app import crud
from app import schemas
from app.bot.api import Api
from app.bot.api.schemas import Message
from app.models import MassDiceEntry, MassDiceBanRecord


class MassBanController:
    active_entries: dict[str, list[schemas.MassDiceEntry]] | None = None

    @classmethod
    def update_active_entries(cls, db: Session):
        entries = crud.mass_dice_entry.get_active_multi(db)
        grouped_entries = {}

        for entry in entries:
            role = entry.target_role
            if role not in grouped_entries:
                grouped_entries[role] = []
            grouped_entries[role].append(entry)
            db.expunge(entry)

        cls.active_entries = grouped_entries

    @classmethod
    async def handle_message(cls, message: Message, db: Session):
        api = Api()

        # sourcery skip: for-append-to-extend
        if cls.active_entries is None:
            cls.update_active_entries(db)

        applied_entries = []
        for role, entries in cls.active_entries.items():
            if role and role not in message.roles:
                continue

            for entry in entries:
                if message.channel_id == entry.channel_id and (
                    not entry.trigger_text
                    or entry.trigger_text in message.content.lower()
                ):
                    applied_entries.append(entry)

        if not applied_entries:
            return

        ban_seconds = len(applied_entries) * 600

        target = message.nick_name
        data = await api.command(f"ban {target} {ban_seconds}", message.channel_id)
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
            if entry.amount == 0:
                asyncio.create_task(cls.finish_mass_entry(entry))

            ban_records.append(
                dict(
                    user_id=message.sender_id,
                    user_nickname=message.nick_name,
                    message=message.content,
                    entry_id=entry.id,
                )
            )

        if ban_records:
            db.execute(insert(MassDiceBanRecord), ban_records)
            db.commit()

    @classmethod
    async def finish_mass_entry(cls, entry: MassDiceEntry):
        api = Api()

        banned_nicknames = list(
            set(map(lambda x: f"@{x.user_nickname}", entry.records))
        )

        target_role_text = (
            f' на роль "{entry.target_role}"' if entry.target_role else ""
        )
        await api.send(
            f"Отчикрыживание от @{entry.issuer_nickname}{target_role_text} окончено! @@ "
            f"Потерпевшие ({len(banned_nicknames)}): {' '.join(banned_nicknames)}",
            entry.channel_id,
        )
