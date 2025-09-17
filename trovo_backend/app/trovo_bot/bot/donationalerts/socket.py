import asyncio

from loguru import logger
from socketio.asyncio_client import AsyncClient

from app.api.deps import get_db
from app.core.config import get_config
from app.trovo_bot.bot.trovo import TrovoApi
from app.utils.singleton import Singleton
from .headers import da_headers


async def get_da_token():
    with next(get_db()) as db:
        token = get_config(db, "da_token")
    return token


class DASocket(AsyncClient, metaclass=Singleton):
    api = TrovoApi()

    _current_media_task: asyncio.Task | None

    def __init__(self, logger=True, engineio_logger=False, **kwargs):
        super().__init__(
            logger=logger,
            engineio_logger=engineio_logger,
            **kwargs,
        )
        self._current_media_task = None
        self.on("disconnect", handler=self.on_disconnect)

    async def connect(
        self,
        url="wss://socket10.donationalerts.ru:443",
        transports=None,
        headers=da_headers,
        *args, **kwargs,
    ):
        if transports is None:
            transports = ["polling"]

        await super().connect(
            url=url, transports=transports, headers=headers, *args, **kwargs
        )

        logger.info("DASocket connected")

        token = await get_da_token()

        await self.emit("add-user", {"token": token, "type": "minor"})
        await self.start_media_loop()

    async def restart_media_loop(self):
        logger.info("Restarting media loop")

        if self._current_media_task:
            self._current_media_task.cancel()

        await self.start_media_loop()

    async def start_media_loop(self):
        logger.info("DASocket media_loop starting")

        self._current_media_task = asyncio.create_task(self.media_loop())

    async def media_loop(self):
        while self.connected:
            token = await get_da_token()

            if await self.api.is_live(self.api.network.channel_id):
                await self.emit_get_current_media(token)

            await asyncio.sleep(60)

    async def emit_get_current_media(self, token):
        logger.info("Sending emit: get-current-media")

        await self.emit(
            "media",
            {
                "token": token,
                "message_data": {
                    "action": "get-current-media",
                },
            },
        )

    async def on_disconnect(self):
        logger.warning("DASocket disconnected")

        self._current_media_task.cancel()

        if self.reconnection:
            self._reconnect_task = self.start_background_task(self._handle_reconnect)

    async def finish(self):
        logger.error("Finishing")

        await self.disconnect()
        await self.wait()


da_sio = DASocket()
