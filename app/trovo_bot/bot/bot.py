import asyncio
import difflib

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.api.deps import get_db
from app.models import DiceAmount
from app.utils.llm import OllamaChatController
from .commands import CommandRegistry
from .commands.modules.cubes import MassBanController
from .commands.modules.mana.utils import get_rank_message
from .trovo import TrovoApi
from .trovo.schemas import Message, MessageType


class Bot:
    def __init__(self):
        self.api = TrovoApi()
        self.db_session = next(get_db())
        self.llm_controller = OllamaChatController()
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

    def get_roles_intersection(self, user_roles: list[str], roles: list[str]):
        roles_lowered = list(map(lambda x: x.lower(), roles))

        intersection = []
        for i in range(len(user_roles)):
            matches = difflib.get_close_matches(user_roles[i].lower(), roles_lowered)
            if matches:
                intersection += user_roles[i]
        print("!!!!!!!!!!!", intersection)

        return intersection

    async def grant_roles(self, nickname: str, roles: list[str], channel_id: int):
        granted_roles = []
        for role in roles:
            data = await self.grant_role(nickname, role, channel_id)
            if data.get("is_success", False):
                granted_roles.append(role)
                break
        return granted_roles

    async def process_mana_spell(self, message: Message):
        gift_num = message.content.get("num", 1)
        gift_value = message.content["gift_value"]
        total_mana = gift_num * gift_value

        mage_roles = [
            "НАЧИНАЮЩИЙ КОЛДУН",
            "HAЧИНАЮЩИЙ КОЛДУН",
            "HАЧИНАЮЩИЙ КОЛДУН",
            "HАЧИНАЮЩИЙ КОЛДУH",
        ]

        mana_intersection = self.get_roles_intersection(message.roles, mage_roles)
        if len(mana_intersection) > 1:
            for i in range(len(mana_intersection) - 1):
                await self.revoke_role(
                    message.nick_name,
                    mana_intersection[i].upper(),
                    message.channel_id,
                    send_message=False,
                )

        if not mana_intersection and total_mana >= 20000:
            granted_mana_roles = await self.grant_roles(
                message.nick_name, mage_roles, message.channel_id
            )
            if not granted_mana_roles:
                await self.api.send(
                    f"У меня не получилось выдать роль {mage_roles[0]} для @{message.nick_name}"
                )

        gifts = {
            "omnomnom": {"required_amount": 1, "roles": ["ОМНОМНОМ", "OМНОМНОМ"]},
            "kfcislive": {"required_amount": 1, "roles": ["ДИЕТОЛОГ"]},
            "shaverma": {"required_amount": 1, "roles": ["ШАУРМАСТЕР", "ШAУРМАСТЕР"]},
            "KAMEHb": {"required_amount": 20, "roles": ["КАМЕНЩИК"]},
            "Pizza": {"required_amount": 1, "roles": ["ПИЦЦА"]},
        }

        for role in gifts.values():
            intersection = self.get_roles_intersection(message.roles, role["roles"])
            if len(intersection) > 1:
                for i in range(len(intersection) - 1):
                    await self.revoke_role(
                        message.nick_name,
                        intersection[i].upper(),
                        message.channel_id,
                        send_message=False,
                    )

        selected_gift = gifts.get(message.content["gift"])

        if not selected_gift:
            return

        logger.info(f"Processing spell {selected_gift}. Message: {message.content}")

        if (
            gift_num >= selected_gift["required_amount"]
            and not self.get_roles_intersection(message.roles, selected_gift["roles"])
        ):
            granted_roles = await self.grant_roles(
                message.nick_name, selected_gift["roles"], message.channel_id
            )
            if not granted_roles:
                await self.api.send(
                    f"У меня не получилось выдать роль {selected_gift['roles']} для @{message.nick_name}"
                )

    async def revoke_role(
        self, nickname: str, role: str, channel_id: int, send_message: bool = True
    ):
        logger.info(f"Revoking role {role} for {nickname} in channel {channel_id}")

        res = await self.api.command(
            f"removerole {role} {nickname}",
            channel_id,
        )
        data = await res.json()

        if send_message:
            if data.get("is_success", False):
                await self.api.send(
                    f'@{nickname} теряет роль "{role}"!',
                    channel_id,
                )
            else:
                await self.api.send(
                    f'У меня не получилось убрать роль "{role}" у @{nickname}. '
                    f"Может быть, я не имею права добавлять роли?",
                    channel_id,
                )

    async def grant_role(
        self, nickname: str, role: str, channel_id: int, send_message: bool = True
    ):
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

        return data

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
        if message.nick_name.lower() in ["fedorbot", "fedorbot2", "jarvisbot"]:
            return

        asyncio.create_task(MassBanController.handle_message(message, self.db_session))

        await self.handle_message_echo(message)

        if message.content.startswith("!"):
            return await self.process_command(message)

        if message.type == MessageType.EVENT:
            return await self.process_event_message(message)

        if message.content.lower().startswith("@jarvisbot"):
            return await self.process_llm_request(message)

        mage_roles = [
            "НАЧИНАЮЩИЙ КОЛДУН",
            "HAЧИНАЮЩИЙ КОЛДУН",
            "HАЧИНАЮЩИЙ КОЛДУН",
            "HАЧИНАЮЩИЙ КОЛДУH",
        ]

        mana_intersection = self.get_roles_intersection(message.roles, mage_roles)
        print("!!!!!!!!!!!!!!!!!!!",mana_intersection)
        if len(mana_intersection) > 1:
            for i in range(len(mana_intersection) - 1):
                await self.revoke_role(
                    message.nick_name,
                    mana_intersection[i].upper(),
                    message.channel_id,
                    send_message=False,
                )


    async def process_command(self, message: Message):
        content_parts = message.content.removeprefix("!").split()
        if not content_parts:
            return

        if command := CommandRegistry.get(content_parts[0].lower()):
            await command.process(content_parts, message)

    async def process_event_message(self, message: Message):
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
                await self.grant_role(
                    nickname, "Чемпион", message.channel_id, send_message=False
                )

    async def process_llm_request(self, message: Message):
        llm_response = await self.llm_controller.handle_message(message)
        await self.api.send(llm_response, message.channel_id)

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
