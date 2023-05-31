import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.api.deps import get_db
from app.models import DiceAmount
from .api import Api
from .api.schemas import Message, MessageType
from .commands import get_commands, CommandBase, CommandInstance, MassCubeCommand
from .commands.modules.mana.utils import get_rank_message


class Bot:
    def __init__(self):
        self.api = Api()
        self.db = self.get_db()
        self.scheduler = None

        CommandBase.set_api(self.api)
        self.commands: dict[str, CommandInstance] = get_commands()
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
        self.scheduler.add_job(self.rocket_rank_job, "cron", minute="50-59")
        self.scheduler.add_job(self.rocket_rank_job, "cron", minute="59", second="30")
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

        if total_mana >= 99999 and "ОМНОМНОМ" not in message.roles:
            await self.api.command(
                f"addrole ОМНОМНОМ {message.nick_name}", self.api.network.channel_id
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
        asyncio.create_task(MassCubeCommand.handle_message(message, self.db))

        if "+ в ча" in message.content.lower():
            await self.api.send("+", self.api.network.channel_id)

        if message.content.startswith("!"):
            await self.process_command(message)

    async def process_command(self, message: Message):
        content_parts = message.content.removeprefix("!").split()

        if command := self.commands.get(content_parts[0].lower()):
            await command.process(content_parts, message)
