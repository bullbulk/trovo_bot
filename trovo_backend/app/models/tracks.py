from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.utils.config import settings


class Track(Base):
    tablename = "track"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str]
    owner: Mapped[str]
    url: Mapped[str]
    date_created: Mapped[datetime]
