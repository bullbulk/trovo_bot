import asyncio
import json
from datetime import datetime
from typing import Callable, Coroutine

from loguru import logger

from app.api.deps import get_db
from app.bot.api import Api
from app.models import Track
from .socket import da_sio

api = Api()


@da_sio.on("media")
async def on_media(data):
    data = json.loads(data)
    if action := data.get("action"):
        logger.info(f"Received media event. Action: {action}")

        if handler := handlers.get(action):
            asyncio.create_task(handler(data))


async def handle_current_media_response(data: dict):
    if (media := data["media"]) and (is_paused := data.get("is_paused")) is not None:
        if not is_paused:
            await api.send(
                f"СЕЙЧАС ИГРАЕТ: :Beats  {media['title']} :Beats ",
                api.network.channel_id,
            )


async def add_track(media: dict):
    logger.info(f"Writing media: {media}")

    with next(get_db()) as db:
        additional = json.loads(media["additional_data"])

        track = Track()
        track.title = media["title"]
        track.owner = additional["owner"]
        track.url = additional["url"]
        track.date_created = datetime.fromisoformat(media["date_created"])

        db.add(track)
        db.commit()


async def handle_add_media_event(data: dict):
    if media := data["media"]:
        await add_track(media)


async def handle_play_media_event(*args):
    await da_sio.restart_media_loop()


handlers: dict[str, Callable[[dict], Coroutine]] = {
    "add": handle_add_media_event,
    "play": handle_play_media_event,
    "receive-current-media": handle_current_media_response,
}
