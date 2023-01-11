import asyncio

from .chat import ChatHandler
from .network import NetworkManager, AuthError
from .socket import ChatSocketProtocol

WEBSOCKET_CLASS = ChatSocketProtocol


class Api:
    chat: ChatHandler
    network: NetworkManager

    def __init__(self):
        self.ready = False
        self.network = NetworkManager()

        asyncio.create_task(self.start())

    async def start(self):
        try:
            await self.network.refresh()
        except AuthError:
            while not self.network.ready:
                await asyncio.sleep(0.1)
        self.chat = ChatHandler(self.network)
        self.ready = True

    async def get_user_info(self):
        return await self.network.get(
            "/getuserinfo"
        )

    async def send(self, content: str, channel_id: int = None):
        data = {
            "content": content
        }
        if channel_id:
            data["channel_id"] = channel_id

        return await self.network.post(
            "/chat/send",
            json=data
        )

    async def delete(self, channel_id: int, message_id: str, user_id: int):
        return await self.network.delete(
            f"/channels/{channel_id}/{message_id}/users/{user_id}",
        )

    async def command(self, command: str, channel_id: int):
        command = command.removeprefix("/")

        return await self.network.post(
            "/channels/command",
            json={
                "command": command,
                "channel_id": channel_id
            }
        )
