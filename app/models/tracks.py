from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class Track(Base):
    __tablename__ = "track"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str]
    owner: Mapped[str]
    url: Mapped[str]
    date_created: Mapped[datetime]
