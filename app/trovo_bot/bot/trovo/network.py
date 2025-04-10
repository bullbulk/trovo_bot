import asyncio
import contextlib
from json import JSONDecodeError
from urllib.parse import urlparse

from aiohttp import ClientSession, ContentTypeError
from loguru import logger

from app.api.deps import get_db
from app.core.config import set_config, get_config
from app.utils.config import settings
from .statuses import (
    INVALID_ACCESS_TOKEN,
    INVALID_REFRESH_TOKEN,
    EXPIRED_ACCESS_TOKEN,
    EXPIRED_REFRESH_TOKEN,
)

REFRESH_TOKEN_ERRORS = (INVALID_REFRESH_TOKEN, EXPIRED_REFRESH_TOKEN)
ACCESS_TOKEN_ERRORS = (INVALID_ACCESS_TOKEN, EXPIRED_ACCESS_TOKEN)

SCOPES = [
    "user_details_self",
    "channel_details_self",
    "channel_update_self",
    "channel_subscriptions",
    "chat_send_self",
    "send_to_my_channel",
    "manage_messages",
]


class AuthError(Exception):
    pass


def get_current_host():
    host = str(settings.SERVER_HOST)
    parsed_host = urlparse(host)
    if parsed_host.hostname == "localhost":
        host = host.replace("localhost", "127.0.0.1")
    return host


class NetworkManager:
    access_token: str | None

    def __init__(self):
        self.access_token = None
        self.need_login = False
        self.ready = asyncio.Event()
        self.channel_id = 0

    async def wait_until_ready(self):
        await self.ready.wait()

    async def get_chat_token(self):
        with next(get_db()) as session:
            channel_nickname = get_config(session, "trovo_channel_nickname")
        if not channel_nickname:
            return

        channel_nickname = channel_nickname.lower()

        await self.update_channel_id(channel_nickname)

        request = await self.get(
            f"/chat/channel-token/{self.channel_id}",
        )
        data = await request.json()
        return data["token"]

    async def update_channel_id(self, nickname: str):
        request = await self.post("/getusers", json={"user": [nickname]})

        data = await request.json()
        users = data.get("users", [{}])

        if not (channel_id := users[0].get("channel_id")):
            return

        self.channel_id = channel_id
        return channel_id

    async def exchange(self, code):
        host = get_current_host()
        body = {
                "client_secret": settings.TROVO_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{host}bot/oauth",
            }
        request = await self.post(
            "/exchangetoken",
            json=body,
        )
        data = await request.json()
        logger.info(data)

        if "access_token" not in data.keys():
            await self._raise_auth_error()
        await self.save_tokens(data["access_token"], data["refresh_token"])
        self.need_login = False

    def get_headers(self):
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Client-Id": settings.TROVO_CLIENT_ID,
            "Authorization": f"OAuth {self.access_token}",
        }

    @staticmethod
    def generate_oauth_uri():
        host = get_current_host()

        return (
            f"https://open.trovo.live/page/login.html"
            f"?client_id={settings.TROVO_CLIENT_ID}"
            f"&response_type=code"
            f"&scope={'+'.join(SCOPES)}"
            f"&redirect_uri={host}bot/oauth"
        )

    async def refresh(self):
        with next(get_db()) as session:
            refresh_token = get_config(session, "refresh_token")
        if not refresh_token:
            return

        request = await self.post(
            "/refreshtoken",
            json={
                "client_secret": settings.TROVO_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )

        data = await request.json()

        if "access_token" not in data.keys():
            await self._raise_auth_error()
        await self.save_tokens(data["access_token"], data["refresh_token"])
        self.need_login = False

    async def save_tokens(self, access: str, refresh: str):
        if refresh:
            with next(get_db()) as session:
                set_config(session, "refresh_token", refresh)
        self.access_token = access
        self.ready.set()

    @staticmethod
    def prepare_url(url: str):
        if not url.startswith("/"):
            url = f"/{url}"
        return url

    async def get(self, url: str, **kwargs):
        async with ClientSession() as session:
            return await self.request(session, "GET", url, **kwargs)

    async def post(self, url: str, **kwargs):
        async with ClientSession() as session:
            return await self.request(session, "POST", url, **kwargs)

    async def delete(self, url: str, **kwargs):
        async with ClientSession() as session:
            return await self.request(session, "DELETE", url, **kwargs)

    async def request(self, session: ClientSession, method: str, url: str, headers=None, **kwargs):
        if headers is None:
            headers = {}

        if not url.startswith("http"):
            url = self.prepare_url(url)
            url = f"{settings.TROVO_API_HOST}{url}"

        headers = {**headers, **self.get_headers()}

        res = await session.request(method, url, headers=headers, **kwargs)

        logger.info(await res.text())

        with contextlib.suppress(JSONDecodeError, ContentTypeError):
            data = await res.json()

            if data.get("status") in ACCESS_TOKEN_ERRORS:
                await self.refresh()
                return await self.request(session, method, url, **kwargs)
            elif data.get("status") in REFRESH_TOKEN_ERRORS:
                await self._raise_auth_error()

        return res

    async def _raise_auth_error(self):
        self.need_login = True
        self.ready.clear()
        raise AuthError()