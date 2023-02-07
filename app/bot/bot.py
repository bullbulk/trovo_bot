import asyncio

from loguru import logger

from app.api.deps import get_db
from app.models import DiceAmount
from .api import Api
from .api.schemas import Message, MessageType
from .commands import get_commands, CommandBase, CommandInstance


class Bot:
    def __init__(self):
        self.api = Api()
        CommandBase.set_api(self.api)

        self.commands: dict[str, CommandInstance] = get_commands()

    async def run(self):
        while not self.api.ready:
            await asyncio.sleep(0.1)

        await self.api.chat.connect()
        self.api.chat.add_listener(self.listen)

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

        if total_mana >= 99999:
            if "ОМНОМНОМ" not in message.roles:
                await self.api.command(
                    f"addrole ОМНОМНОМ {message.nick_name}",
                    self.api.network.channel_id
                )

    async def process_dice_spell(self, message: Message):
        num = message.content["num"]

        db = self.get_db()

        dice_amount = db.query(DiceAmount).filter(DiceAmount.user_id == message.sender_id).first()
        if not dice_amount:
            dice_amount = DiceAmount(user_id=message.sender_id, amount=num)
        else:
            dice_amount.amount += num
        db.add(dice_amount)
        db.commit()
        db.refresh(dice_amount)
        db.close()

    async def process_message(self, message: Message):
        if "+ в чат" in message.content.lower():
            await self.api.send(
                "+",
                self.api.network.channel_id
            )

        if message.content.startswith("!"):
            await self.process_command(message)

    async def process_command(self, message: Message):
        content_parts = message.content.removeprefix("!").split()

        if command := self.commands.get(content_parts[0].lower()):
            await command.process(content_parts, message)
