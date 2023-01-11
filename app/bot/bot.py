import asyncio

from loguru import logger

from app.api.deps import get_db
from app.models import DiceAmount
from .api import Api
from .api.schemas import Message, MessageType


class Bot:
    api = Api()

    async def run(self):
        while not self.api.ready:
            await asyncio.sleep(0.1)

        await self.api.chat.connect()
        self.api.chat.add_listener(self.listen)

    @staticmethod
    def get_db():
        return next(get_db())

    async def listen(self, message: Message):
        logger.info(message.content)
        if message.type in [MessageType.SPELL, MessageType.SPELL_CUSTOM]:
            asyncio.create_task(self.process_spell(message))

    async def process_spell(self, message: Message):
        logger.info(f"{message.send_time, message.nick_name, message.content}")

        if message.content.get("gift") == "Dice":
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
