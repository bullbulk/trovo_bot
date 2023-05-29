import asyncio
import json
import traceback
from asyncio import Task
from datetime import datetime
from typing import Callable, Awaitable, TypeVar

import websockets
from loguru import logger
from pydantic import ValidationError
from websockets.exceptions import ConnectionClosedError

from app.config import settings
from .network import NetworkManager
from .schemas import WebSocketMessage, Message, WebSocketMessageType
from .socket import ChatSocketProtocol

WEBSOCKET_PROTOCOL_CLASS = ChatSocketProtocol

AsyncMessageCallback = TypeVar(
    "AsyncMessageCallback", bound=Callable[[Message], Awaitable[None]]
)


class ChatHandler:
    socket: ChatSocketProtocol | None
    listener_task: Task | None
    connecting_task: Task | None
    listeners: list[AsyncMessageCallback]
    start_timestamp: float | None

    def __init__(self, network: NetworkManager):
        self.network = network
        self.listeners = []
        self.running = False
        self.start_timestamp = None
        self.socket = None
        self.listener_task = None
        self.connecting_task = None

    def add_listener(self, callback: AsyncMessageCallback):
        self.listeners.append(callback)

    async def connect(self):
        await self.stop()
        self.connecting_task = asyncio.create_task(self._connect())

    async def stop(self):
        if self.connecting_task:
            self.connecting_task.cancel()
        if self.listener_task:
            self.listener_task.cancel()
        if self.socket:
            await self.socket.close()
        self.running = False

    async def _connect(self):
        if self.running:
            return

        if not self.network.access_token:
            await self.network.refresh()

        logger.info("Connecting")

        self.socket = await websockets.connect(
            settings.TROVO_WEBSOCKET_HOST,
            create_protocol=WEBSOCKET_PROTOCOL_CLASS,
            ping_interval=None,
            ping_timeout=None,
        )
        self.listener_task = asyncio.create_task(self.listen())
        self.socket.set_network_manager(self.network)
        await self.socket.auth()
        self.start_timestamp = datetime.now().timestamp()
        self.running = True

        logger.info("Connected")

    async def listen(self):
        try:
            async for message in self.socket:
                if message.type == WebSocketMessageType.PONG:
                    if gap := message.data.get("gap"):
                        self.socket.set_ping_gap(gap)

                if message.type != WebSocketMessageType.CHAT:
                    continue

                if isinstance(message.data, dict):
                    logger.warning(message.origin_string)
                    continue

                for chat in message.data.chats:
                    if chat.send_time.timestamp() < self.start_timestamp:
                        continue

                    for callback in self.listeners:
                        asyncio.create_task(callback(chat))

        except ConnectionClosedError:
            logger.warning("Connection closed")
            self.running = False
            try:
                return await self.connect()
            except Exception:
                logger.error("Unable to connect")
        except Exception:
            logger.error(traceback.format_exc())
