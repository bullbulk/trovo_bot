from enum import Enum

from pydantic import BaseModel


class TokenScope(Enum):
    ACCESS = "access_token"
    REFRESH = "refresh_token"


class TokenType(Enum):
    BEARER = "bearer"


class Token(BaseModel):
    token: str
    token_scope: TokenScope


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: TokenType


class TokenPayload(BaseModel):
    sub: int | None
    scope: TokenScope
