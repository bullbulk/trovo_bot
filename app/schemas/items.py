from datetime import datetime

from pydantic import BaseModel, AnyHttpUrl


class Track(BaseModel):
    id: int
    title: str
    owner: str
    url: AnyHttpUrl
    created_at: datetime

    class Config:
        orm_mode = True
