import asyncio

from loguru import logger
from socketio.asyncio_client import AsyncClient

from app.api.deps import get_db
from app.bot.api import Api
from app.core.config import get_config
from app.singleton import Singleton
from .headers import da_headers


class DASocket(AsyncClient, metaclass=Singleton):
    api = Api()

    _current_media_task: asyncio.Task | None

    def __init__(
        self,
        reconnection=True,
        reconnection_attempts=0,
        reconnection_delay=1,
        reconnection_delay_max=5,
        randomization_factor=0.5,
        logger=True,
        engineio_logger=True,
        binary=False,
        json=None,
        **kwargs,
    ):
        super().__init__(
            reconnection=reconnection,
            reconnection_attempts=reconnection_attempts,
            reconnection_delay=reconnection_delay,
            reconnection_delay_max=reconnection_delay_max,
            randomization_factor=randomization_factor,
            logger=logger,
            engineio_logger=engineio_logger,
            binary=binary,
            json=json,
            **kwargs,
        )
        self._current_media_task = None
        self.on("disconnect", handler=self.on_disconnect)

    async def connect(
        self,
        url="wss://socket10.donationalerts.ru:443",
        transports=None,
        headers=da_headers,
        *args,
        **kwargs,
    ):
        if transports is None:
            transports = ["polling"]

        await super().connect(
            url=url, transports=transports, headers=headers, *args, **kwargs
        )

        logger.info("DASocket connected")

        with next(get_db()) as db:
            token = get_config(db, "da_token")

        await self.emit("add-user", {"token": token, "type": "minor"})
        await self.start_media_loop()

    async def restart_media_loop(self):
        logger.info("Restarting media loop")

        if self._current_media_task:
            self._current_media_task.cancel()

        await self.start_media_loop()

    async def start_media_loop(self):
        logger.info("DASocket media_loop started")
        self._current_media_task = asyncio.create_task(self.media_loop())

    async def media_loop(self):
        while self.connected:
            with next(get_db()) as db:
                token = get_config(db, "da_token")

            res = await self.api.get_channel_info(self.api.network.channel_id)
            data = await res.json()

            if data.get("is_live"):
                await self.emit_get_current_media(token)

            await asyncio.sleep(30)

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
