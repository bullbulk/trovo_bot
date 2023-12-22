import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.api.deps import get_db
from app.models import DiceAmount
from .commands import CommandRegistry
from .commands.modules.cubes import MassBanController
from .commands.modules.mana.utils import get_rank_message
from .trovo import TrovoApi
from .trovo.schemas import Message, MessageType


class Bot:
    def __init__(self):
        self.api = TrovoApi()
        self.db_session = next(get_db())
        self.scheduler = None

        self.setup_scheduler()

    async def run(self):
        await self.api.start()
        await self.api.wait_until_ready()

        await self.api.chat.connect()
        await self.api.chat.connecting_task

        asyncio.create_task(self.connect_da())

        self.api.chat.add_listener(self.listen)

    async def connect_da(self):
        # await da_sio.connect()
        ...

    async def rocket_rank_job(self):
        if await self.api.is_live(self.api.network.channel_id):
            msg = await get_rank_message(self.api.network.channel_id)

            await self.api.send(
                msg,
                self.api.network.channel_id,
            )

    def setup_scheduler(self):
        if self.scheduler:
            return

        self.scheduler = AsyncIOScheduler()

        self.scheduler.add_job(
            self.rocket_rank_job,
            "cron",
            minute="50-59",
            hour="5-21",
            day_of_week="0-5",
        )
        self.scheduler.add_job(
            self.rocket_rank_job,
            "cron",
            minute="59",
            second="30",
            hour="5-21",
            day_of_week="0-5",
        )

        self.scheduler.start()

    async def listen(self, message: Message):
        if message.is_spell:
            asyncio.create_task(self.process_spell(message))

        if message.type == MessageType.NORMAL:
            asyncio.create_task(self.process_message(message))

    async def process_spell(self, message: Message):
        logger.info(
            f"{message.send_time.strftime('%m/%d/%Y, %H:%M:%S.%f')} {message.nick_name} "
            f"{message.sender_id} {message.content}"
        )

        if message.content.get("gift") == "MrCube":
            await self.process_dice_spell(message)

        if message.content.get("value_type") == "Mana":
            await self.process_mana_spell(message)

    async def process_mana_spell(self, message: Message):
        gift_num = message.content.get("num", 1)
        gift_value = message.content["gift_value"]
        total_mana = gift_num * gift_value

        if total_mana >= 20000:
            await self.grant_role(message.nick_name, "HАЧИНАЮЩИЙ КОЛДУН", message.channel_id)

        gifts = {
            "omnomnom": {"required_amount": 1, "role": "ОМНОМНОМ"},
            "kfcislive": {"required_amount": 1, "role": "ДИЕТОЛОГ"},
            "shaverma": {"required_amount": 1, "role": "ШАУРМАСТЕР"},
            "Megalodon": {"required_amount": 999, "role": "МЕГАЛОМАСТЕР"},
        }

        selected_gift = gifts.get(message.content["gift"])

        if not selected_gift:
            return

        logger.info(f"Processing spell {selected_gift}. Message: {message.content}")

        if (
            gift_num >= selected_gift["required_amount"]
            and (selected_role := selected_gift["role"]) not in message.roles
        ):
            await self.grant_role(message.nick_name, selected_role, message.channel_id)

    async def grant_role(self, nickname: str, role: str, channel_id: int, send_message: bool = True):
        logger.info(f"Granting role {role} for {nickname} in channel {channel_id}")

        res = await self.api.command(
            f"addrole {role} {nickname}",
            channel_id,
        )
        data = await res.json()

        if send_message:
            if data.get("is_success", False):
                await self.api.send(
                    f'@{nickname} получает роль "{role}"!',
                    channel_id,
                )
            else:
                await self.api.send(
                    f'У меня не получилось выдать роль "{role}" для @{nickname}. '
                    f"Может быть, я не имею права добавлять роли?",
                    channel_id,
                )

    async def process_dice_spell(self, message: Message):
        num = message.content["num"]

        db = next(get_db())

        dice_amount = (
            db.query(DiceAmount).filter(DiceAmount.user_id == message.sender_id).first()
        )
        if not dice_amount:
            dice_amount = DiceAmount(user_id=message.sender_id, amount=num)  # noqa
        else:
            dice_amount.amount += num
        db.add(dice_amount)
        db.commit()
        db.close()

    async def process_message(self, message: Message):
        asyncio.create_task(MassBanController.handle_message(message, self.db_session))

        await self.handle_message_echo(message)

        if message.content.startswith("!"):
            await self.process_command(message)

    async def process_command(self, message: Message):
        content_parts = message.content.removeprefix("!").split()
        if not content_parts:
            return

        if command := CommandRegistry.get(content_parts[0].lower()):
            await command.process(content_parts, message)

    async def process_activity_message(self, message: Message):
        if message.content_data.get("activity_topic") == "shooter_space_boss_defeated":
            pass
            # return await self.grant_role(message, "SHOOTER")
        logger.info(message.content_data)
        if (
            message.content_data.get("activity_ext", {}).get("title", {}).get("i18nKey")
        ) == "pk.wintitle":
            logger.info("Captured PK Win")
            for user in message.content_data["at"]:
                nickname = user["name"]
                await self.grant_role(nickname, "Чемпион", message.channel_id, send_message=False)

    async def handle_message_echo(self, message: Message):
        echoes = {
            "+ в ча": "+",
            "юпуп": ":sub_peepoclogi",
        }

        text = message.content.lower()

        for trigger, value in echoes.items():
            if trigger in text:
                await self.api.send(value, message.channel_id)
                break
