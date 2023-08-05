import asyncio
import json
import time
import traceback
from asyncio import Future
from typing import Optional

from loguru import logger
from pydantic import ValidationError
from websockets.legacy.client import WebSocketClientProtocol

from app.utils import get_rand_string
from .network import NetworkManager
from .schemas import WebSocketMessage, WebSocketMessageType


class PingController:
    socket: WebSocketClientProtocol
    _task: asyncio.Task
    gap = 25
    ping_timeout = 10

    def __init__(self, socket):
        self.socket = socket
        self.pings: dict[str, [Future, float]] = {}

    def start(self):
        self._task = asyncio.create_task(self.loop())

    def set_ping_gap(self, gap: int):
        self.gap = gap

    async def ping(self, type_="PING", **data):
        nonce = get_rand_string()
        await self.socket.send(json.dumps({"type": type_, "nonce": nonce, **data}))
        logger.debug("sent keepalive ping")

        pong_waiter = self.socket.loop.create_future()
        ping_timestamp = time.perf_counter()
        self.pings[nonce] = (pong_waiter, ping_timestamp)

        try:
            await asyncio.wait_for(
                pong_waiter,
                self.ping_timeout,
            )
            logger.debug("received keepalive pong")
        except asyncio.TimeoutError:
            logger.error("keepalive ping timeout")
            await self.socket.close()

    async def loop(self):
        while True:
            await asyncio.sleep(self.gap)
            await self.ping()

    def stop(self):
        if hasattr(self, "_task"):
            self._task.cancel()
        self.pings.clear()

    async def process_pong(self, message: WebSocketMessage):
        if ping_data := self.pings.get(message.nonce):
            pong_waiter, ping_timestamp = ping_data
            if not pong_waiter.done():
                pong_timestamp = time.perf_counter()
                pong_waiter.set_result(pong_timestamp - ping_timestamp)

            del self.pings[message.nonce]


class ChatSocketProtocol(WebSocketClientProtocol):
    ping_controller: PingController | None
    network: NetworkManager

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ping_controller = None

    def connection_open(self) -> None:
        super().connection_open()

        self.ping_controller = PingController(self)
        self.ping_controller.start()

    async def auth(self):
        await self.ping_controller.ping(
            type="AUTH",
            data={"token": await self.network.get_chat_token()},
        )

    def set_network_manager(self, manager: NetworkManager):
        self.network = manager

    def connection_lost(self, exc: Optional[Exception]) -> None:
        if self.ping_controller:
            self.ping_controller.stop()
        return super().connection_lost(exc)

    async def recv(self) -> WebSocketMessage:
        message = await super().recv()
        try:
            data = WebSocketMessage(origin_string=message, **json.loads(message))
            if data.nonce and data.type in (
                WebSocketMessageType.PONG,
                WebSocketMessageType.RESPONSE,
            ):
                if gap := data.data.get("gap"):
                    self.ping_controller.set_ping_gap(gap)
                await self.ping_controller.process_pong(data)
            return data
        except ValidationError:
            logger.error(traceback.format_exc())
