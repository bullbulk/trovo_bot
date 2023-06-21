from pydantic import BaseModel


class OAuthUri(BaseModel):
    uri: str


class MassDiceBanRecord(BaseModel):
    user_id: int
    user_nickname: str
    entry_id: int


class MassDiceEntry(BaseModel):
    issuer_id: int
    issuer_nickname: str
    amount: int
    trigger_text: str
    target_role: str | None
    channel_id: str
