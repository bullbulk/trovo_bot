import json
from datetime import datetime
from enum import Enum
from json import JSONDecodeError
from typing import Literal, Any

from pydantic import BaseModel, validator, root_validator, Field, field_validator, ValidationError
from unidecode import unidecode


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
    avatar: str | None = Field(default=None)
    sub_lv: SubLvl = SubLvl.L0
    sub_tier: Literal[0, 1, 2, 3] = 0
    medals: list[str] = Field(default_factory=list)
    decos: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    ascii_roles: list[str] = Field(default_factory=list)
    message_id: str
    sender_id: int | None = Field(default=None)
    send_time: datetime
    uid: int | None = Field(default=None)
    user_name: str | None = Field(default=None)
    content_data: dict[str, Any] = Field(default_factory=dict)
    # custom_role: list[RoleData]
    custom_role: str | None = Field(default=None)

    @validator("sub_tier", pre=True)
    def validate_sub_tier(cls, v):  # noqa
        return int(v)

    @validator("content", pre=True)
    def validate_content(cls, v):  # noqa
        try:
            return json.loads(v)
        except JSONDecodeError:
            return v

    @root_validator(pre=True)
    def build_roles(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "roles" in values:
            values["ascii_roles"] = list(
                map(lambda x: unidecode(x.lower()), values["roles"])
            )
        return values

    @property
    def channel_id(self):
        # message_id is presented as "messageId_channelId_senderId_..."
        return self.message_id.split("_")[1]

    @property
    def is_spell(self):
        return self.type in [MessageType.SPELL, MessageType.SPELL_CUSTOM]


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
    origin_string: str

    type: WebSocketMessageType
    channel_info: ChannelInfo | None = Field(default=None)
    data: WebSocketMessageData | dict[str, Any] = Field(default_factory=dict)
    nonce: str | None = Field(default=None)

    @field_validator("data")
    def validate_data(cls, v: dict[str, Any]):
        try:
            return WebSocketMessageData(**v)
        except ValidationError:
            return v
