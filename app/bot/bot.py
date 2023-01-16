import asyncio
from random import randint
from typing import TypeVar, Awaitable, Callable

from loguru import logger

from app.api.deps import get_db
from app.models import DiceAmount
from .api import Api
from .api.schemas import Message, MessageType

CommandFunction = TypeVar("CommandFunction", bound=Callable[[list[str], Message], Awaitable[None]])


class Bot:
    api: Api
    commands: dict[str, CommandFunction]

    def __init__(self):
        self.api = Api()

        self.commands: dict[str, CommandFunction] = {
            "отпежить": self.cube,
            "баланс": self.balance,
            "help": self.help,
        }

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
            f"{message.send_time.strftime('%m/%d/%Y, %H:%M:%S.%f'), message.nick_name} "
            f"{message.sender_id, message.content}"
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
            await command(content_parts, message)

    async def cube(self, parts: list[str], message: Message):
        try:
            target = parts[1]
            target = target.removeprefix("@")
            if target.lower() in ["fedorbot2", "fedorbot"]:
                await self.api.send(
                    f"@{message.nick_name} анус свой отпежь, пёс",
                    self.api.network.channel_id
                )
                return

            amount = 1
            if len(parts) >= 3:
                if parts[2].isnumeric():
                    amount = int(parts[2])
                if amount <= 0:
                    amount = 1

        except IndexError:
            await self.api.send(
                "Использование: !отпежить <никнейм>",
                self.api.network.channel_id
            )
            return

        db = self.get_db()

        dice_amount = db.query(DiceAmount).filter(DiceAmount.user_id == message.sender_id).first()

        if dice_amount:
            dice_amount_num = dice_amount.amount
        else:
            dice_amount_num = 0

        if dice_amount_num < amount:
            await self.api.send(
                f"@{message.nick_name} у тебя недостаточно кубов",
                self.api.network.channel_id
            )
            return

        dices_results = {}

        for i in range(amount):
            result = randint(1, 6)
            if dices_results.get(result):
                dices_results[result] += 1
            else:
                dices_results[result] = 1

        success_dices_num = sum([y for x, y in dices_results.items() if x > 3])
        result_str = ", ".join(
            [f"{x} ({y} шт.)" for x, y in sorted(
                dices_results.items(), key=lambda v: v[0]
            )]
        )

        subtract_cubes = False

        if not success_dices_num:
            await self.api.send(
                f"@{message.nick_name} результат: {result_str}, {target} выживает",
                self.api.network.channel_id
            )
            subtract_cubes = True
        else:
            ban_seconds = success_dices_num * 600

            data = await self.api.command(
                f"ban {target} {ban_seconds}",
                self.api.network.channel_id
            )
            data = await data.json()

            if data.get("is_success"):
                await self.api.send(
                    f"@{message.nick_name} результат: {result_str}, "
                    f"{target} отлетает на {ban_seconds // 60} минут",
                    self.api.network.channel_id
                )
                subtract_cubes = True

            else:
                await self.api.send(
                    f"@{message.nick_name} результат: {result_str}, "
                    f"{target} должен был отлететь на {ban_seconds // 60} минут, "
                    f"но при мьюте произошла ошибка. "
                    f"Возможно, ты неправильно написал ник или пользователь уже в бане",
                    self.api.network.channel_id
                )

        if subtract_cubes:
            dice_amount.amount -= amount
            db.add(dice_amount)
            db.commit()
            db.refresh(dice_amount)

    async def help(self, parts: list[str], message: Message):
        response = f"Команды: {', '.join(list(self.commands.keys()))}"

        await self.api.send(
            response,
            self.api.network.channel_id
        )

    async def balance(self, parts: list[str], message: Message):
        target_id = None
        target = None

        if len(parts) > 1:
            target = parts[1].removeprefix("@")
            if target not in ["fedorbot", "fedorbot2"]:
                request = await self.api.get_users([target])
                data = await request.json()

                users = data.get("users", [{}])
                target_id = users[0].get("channel_id")

        if not target_id:
            target_id = message.sender_id

        db = self.get_db()

        dice_amount = db.query(DiceAmount).filter(DiceAmount.user_id == target_id).first()
        if dice_amount:
            result_amount = dice_amount.amount
        else:
            result_amount = 0

        if target_id == message.sender_id:
            response_message = f"@{message.nick_name} кубов у тебя на счету: {result_amount}"
        else:
            response_message = f"@{message.nick_name} кубов на счету у {target}: {result_amount}"

        await self.api.send(
            response_message,
            self.api.network.channel_id
        )
