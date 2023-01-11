import asyncio
import json
from typing import Optional

from websockets.legacy.client import WebSocketClientProtocol

from .network import NetworkManager


class Timer:
    socket: WebSocketClientProtocol
    _task: asyncio.Task
    gap = 25

    def __init__(self, socket):
        self.socket = socket

    def start(self):
        self._task = asyncio.create_task(self.loop())

    async def loop(self):
        while True:
            await asyncio.sleep(self.gap)
            await self.socket.send(
                json.dumps(
                    {
                        "type": "PING",
                        "nonce": "nonce"
                    }
                )
            )

    def stop(self):
        if hasattr(self, "_task"):
            self._task.cancel()


class ChatSocketProtocol(WebSocketClientProtocol):
    timer: Timer | None
    network: NetworkManager

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timer = None

    def connection_open(self) -> None:
        super().connection_open()

        self.timer = Timer(self)
        self.timer.start()

    async def auth(self):
        await self.send(
            json.dumps(
                {
                    "type": "AUTH",
                    "nonce": "nonce",
                    "data": {
                        "token": await self.network.get_chat_token()
                    }
                }
            )
        )

    def set_ping_gap(self, gap: int):
        self.timer.gap = gap

    def set_network_manager(self, manager: NetworkManager):
        self.network = manager

    def connection_lost(self, exc: Optional[Exception]) -> None:
        if self.timer:
            self.timer.stop()
        return super().connection_lost(exc)
