from json import JSONDecodeError

from aiohttp import ClientSession, ContentTypeError
from loguru import logger

from app.api.deps import get_db
from app.config import settings
from app.core.config import set_config, get_config
from .statuses import (
    INVALID_ACCESS_TOKEN, 
    INVALID_REFRESH_TOKEN,
    EXPIRED_ACCESS_TOKEN,
    EXPIRED_REFRESH_TOKEN
)


scopes = [
    "user_details_self", "channel_details_self",
    "channel_update_self", "channel_subscriptions",
    "chat_send_self", "send_to_my_channel",
    "manage_messages"
]


class AuthError(Exception):
    pass


class NetworkManager:
    access_token: str | None

    def __init__(self):
        self.access_token = None
        self.need_login = False
        self.ready = False
        self.channel_id = 0

    async def get_chat_token(self):
        channel_nickname = get_config(self.get_db(), 'trovo_channel_nickname')
        if not channel_nickname:
            return

        channel_nickname = channel_nickname.value.lower()

        await self.update_channel_id(channel_nickname)

        request = await self.get(
            f"/chat/channel-token/{self.channel_id}",
        )
        data = await request.json()
        return data["token"]

    async def update_channel_id(self, nickname: str):
        request = await self.post(
            "/getusers",
            json={"user": [nickname]}
        )

        data = await request.json()
        users = data.get("users", [{}])

        if not (channel_id := users[0].get("channel_id")):
            return

        self.channel_id = channel_id
        return channel_id

    async def exchange(self, code):
        request = await self.post(
            "/exchangetoken",
            json={
                "client_secret": settings.TROVO_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{settings.SERVER_HOST}{settings.API_V1_STR}/bot/oauth"
            },
        )
        data = await request.json()
        logger.info(data)

        if "access_token" not in data.keys():
            self.need_login = True
            raise AuthError()
        await self.save_tokens(data["access_token"], data["refresh_token"])
        self.need_login = False

    def get_headers(self):
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Client-Id": settings.TROVO_CLIENT_ID,
            "Authorization": f"OAuth {self.access_token}"
        }

    @staticmethod
    def generate_oauth_uri():
        return \
            f"https://open.trovo.live/page/login.html" \
            f"?client_id={settings.TROVO_CLIENT_ID}" \
            f"&response_type=code" \
            f"&scope={'+'.join(scopes)}" \
            f"&redirect_uri={settings.SERVER_HOST}/api/v1/bot/oauth"

    async def refresh(self):
        refresh_token = get_config(self.get_db(), "refresh_token")
        if not refresh_token:
            return
        if not refresh_token.value:
            return

        request = await self.post(
            "/refreshtoken",
            json={
                "client_secret": settings.TROVO_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token.value,
            },
        )

        data = await request.json()

        if "access_token" not in data.keys():
            self.need_login = True
            raise AuthError()
        await self.save_tokens(data["access_token"], data["refresh_token"])
        self.need_login = False

    async def save_tokens(self, access: str, refresh: str):
        set_config(self.get_db(), "refresh_token", refresh)
        self.access_token = access
        self.ready = True

    @staticmethod
    def get_db():
        return next(get_db())

    @staticmethod
    def prepare_url(url: str):
        if not url.startswith("/"):
            url = "/" + url
        return url

    async def get(self, url: str, **kwargs):
        async with ClientSession() as session:
            res = await self.request(session, "GET", url, **kwargs)
            return res

    async def post(self, url: str, **kwargs):
        async with ClientSession() as session:
            res = await self.request(session, "POST", url, **kwargs)
            return res

    async def delete(self, url: str, **kwargs):
        async with ClientSession() as session:
            res = await self.request(session, "DELETE", url, **kwargs)
            return res

    async def request(self, session: ClientSession, method: str, url: str, **kwargs):
        if not url.startswith("http"):
            url = self.prepare_url(url)
            url = f"{settings.TROVO_API_HOST}{url}"

        if not kwargs.get("headers"):
            kwargs["headers"] = {}
        kwargs["headers"] = {**kwargs["headers"], **self.get_headers()}

        res = await session.request(method, url, **kwargs)

        logger.info(await res.text())

        try:
            data = await res.json()

            if data.get("status") in (INVALID_ACCESS_TOKEN, EXPIRED_ACCESS_TOKEN):
                await self.refresh()
                return await self.request(session, method, url, **kwargs)
            elif data.get("status") in (INVALID_REFRESH_TOKEN, EXPIRED_REFRESH_TOKEN):
                self.ready = False
                raise AuthError()

        except (JSONDecodeError, ContentTypeError):
            pass

        return res
