from pydantic import BaseModel


class OAuthUri(BaseModel):
    uri: str
