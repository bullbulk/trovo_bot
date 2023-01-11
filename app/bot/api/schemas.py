import json
from datetime import datetime
from enum import Enum
from json import JSONDecodeError
from typing import Literal, Any

from pydantic import BaseModel, validator


class MessageType(Enum):
    NORMAL = 0
    SPELL = 5
    MAGIC_SUPER_CAP = 6
    MAGIC_COLORFUL = 7
    MAGIC_SPELL = 8
    MAGIC_BULLET = 9
    SUBSCRIPTION = 5001
    SYSTEM = 5002
    FOLLOW = 5003
    WELCOME = 5004
    GIFT_SUB_RANDOM = 5005
    GIFT_SUB_TARGET = 5006
    EVENT = 5007
    WELCOME_RAID = 5008
    SPELL_CUSTOM = 5009
    STREAM_STATUS = 5012
    UNFOLLOW = 5013


class RoleType(Enum):
    STREAMER = 100000
    MODERATOR = 100001
    EDITOR = 100002
    SUBSCRIBER = 100004
    SUPERMOD = 100005
    FOLLOWER = 100006
    CUSTOM = 200000
    ADMIN = 500000
    WARDEN = 500001
    ACE = 300000
    ACE_PLUS = 300001


class SubLvl(Enum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"


class RoleData(BaseModel):
    roleName: str
    roleType: RoleType


class Message(BaseModel):
    type: MessageType
    content: dict[str, Any] | str
    nick_name: str
    avatar: str | None
    sub_lv: SubLvl = SubLvl.L0
    sub_tier: Literal[0, 1, 2, 3] = 0
    medals: list[str] = []
    decos: list[str] = []
    roles: list[str] = []
    message_id: str
    sender_id: int | None
    send_time: datetime
    uid: int | None
    user_name: str | None
    content_data: dict[str, Any] = {}
    # custom_role: list[RoleData]
    custom_role: str | None

    @validator("sub_tier", pre=True)
    def validate_sub_tier(cls, v):  # noqa
        return int(v)

    @validator("content", pre=True)
    def validate_content(cls, v):  # noqa
        try:
            return json.loads(v)
        except JSONDecodeError:
            return v


class WebSocketMessageData(BaseModel):
    eid: str
    chats: list[Message]


class ChannelInfo(BaseModel):
    channel_id: str


class WebSocketMessageType(Enum):
    CHAT = "CHAT"
    RESPONSE = "RESPONSE"
    PING = "PING"
    PONG = "PONG"
    AUTH = "AUTH"


class WebSocketMessage(BaseModel):
    type: WebSocketMessageType
    channel_info: ChannelInfo | None
    data: WebSocketMessageData | dict[str, Any] = {}
    nonce: str | None
