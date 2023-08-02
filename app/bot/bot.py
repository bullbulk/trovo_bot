import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.api.deps import get_db
from app.models import DiceAmount
from .api import Api
from .api.schemas import Message, MessageType
from .commands import CommandRegistry
from .commands.modules.cubes.controllers.massban import MassBanController
from .commands.modules.mana.utils import get_rank_message


class Bot:
    def __init__(self):
        self.api = Api()
        self.db = self.get_db()
        self.scheduler = None

        self.setup_scheduler()

    async def run(self):
        while not self.api.ready:
            await asyncio.sleep(0.1)

        await self.api.chat.connect()
        self.api.chat.add_listener(self.listen)

    async def rocket_rank_job(self):
        res = await self.api.get_channel_info(self.api.network.channel_id)
        data = await res.json()

        if data.get("is_live"):
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
            hour="0-21",
            day_of_week="0-5",
        )
        self.scheduler.add_job(
            self.rocket_rank_job,
            "cron",
            minute="59",
            second="30",
            hour="0-21",
            day_of_week="0-5",
        )

        self.scheduler.start()

    @staticmethod
    def get_db():
        return next(get_db())

    async def listen(self, message: Message):
        if message.type in [MessageType.SPELL, MessageType.SPELL_CUSTOM]:
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
        total_mana = message.content["num"] * message.content["gift_value"]

        if total_mana >= 20000:
            await self.grant_role(message, "НАЧИНАЮЩИЙ КОЛДУН")

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
            message.content["num"] >= selected_gift["required_amount"]
            and (selected_role := selected_gift["role"]) not in message.roles
        ):
            await self.grant_role(message, selected_role)

    async def grant_role(self, message: Message, role: str):
        if role in message.roles:
            return

        res = await self.api.command(
            f"addrole {role} {message.nick_name}",
            message.channel_id,
        )
        data = await res.json()
        if data.get("is_success", False):
            await self.api.send(
                f'@{message.nick_name} получает роль "{role}"!',
                message.channel_id,
            )
        else:
            await self.api.send(
                f'У меня не получилось выдать роль "{role}" для @{message.nick_name}. '
                f"Может быть, я не имею права добавлять роли?",
                message.channel_id,
            )

    async def process_dice_spell(self, message: Message):
        num = message.content["num"]

        db = self.get_db()

        dice_amount = (
            db.query(DiceAmount).filter(DiceAmount.user_id == message.sender_id).first()
        )
        if not dice_amount:
            dice_amount = DiceAmount(user_id=message.sender_id, amount=num)  # noqa
        else:
            dice_amount.amount += num
        db.add(dice_amount)
        db.commit()
        db.refresh(dice_amount)
        db.close()

    async def process_message(self, message: Message):
        asyncio.create_task(MassBanController.handle_message(message, self.db))

        await self.handle_message_echo(message)

        if message.content.startswith("!"):
            await self.process_command(message)

    async def process_command(self, message: Message):
        content_parts = message.content.removeprefix("!").split()

        if command := CommandRegistry.get(content_parts[0].lower()):
            await command.process(content_parts, message)

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
