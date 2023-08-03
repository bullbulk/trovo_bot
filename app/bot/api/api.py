import asyncio

from app.singleton import Singleton
from .chat import ChatHandler
from .network import NetworkManager, AuthError
from .socket import ChatSocketProtocol

WEBSOCKET_CLASS = ChatSocketProtocol


class Api(metaclass=Singleton):
    chat: ChatHandler
    network: NetworkManager

    def __init__(self):
        self.ready = asyncio.Event()
        self.network = NetworkManager()

        asyncio.create_task(self.start())

    async def start(self):
        try:
            await self.network.refresh()
        except AuthError:
            await self.network.wait_until_ready()
        self.chat = ChatHandler(self.network)
        self.ready.set()

    async def wait_until_ready(self):
        await self.ready.wait()

    async def get_user_info(self):
        return await self.network.get("/getuserinfo")

    async def get_channel_info(
        self,
        channel_id: int | None = None,
        username: str | None = None,
    ):
        data = {}
        if channel_id:
            data["channel_id"] = channel_id
        if username:
            data["username"] = username

        if not data:
            raise ValueError("channel_id or username should be provided.")

        return await self.network.post("/channels/id", json=data)

    async def get_users(self, nicknames: list[str]):
        return await self.network.post("/getusers", json={"user": nicknames})

    async def send(self, content: str, channel_id: int = None):
        data = {"content": content}
        if channel_id:
            data["channel_id"] = channel_id

        return await self.network.post("/chat/send", json=data)

    async def delete(self, channel_id: int, message_id: str, user_id: int):
        return await self.network.delete(
            f"/channels/{channel_id}/{message_id}/users/{user_id}",
        )

    async def command(self, command: str, channel_id: str | int):
        command = command.removeprefix("/")

        return await self.network.post(
            "/channels/command", json={"command": command, "channel_id": channel_id}
        )

    async def is_live(self, channel_id: int):
        res = await self.get_channel_info(channel_id)
        data = await res.json()
        return data.get("is_live", False)