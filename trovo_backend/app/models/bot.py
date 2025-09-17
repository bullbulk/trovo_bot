from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, CheckConstraint, func
from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.db.base_class import Base


class DiceAmount(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(index=True)
    amount: Mapped[int] = mapped_column()


class MassDiceEntry(Base):
    __tablename__ = "mass_dice_entry"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    channel_id: Mapped[str] = mapped_column(server_default="0")
    issuer_id: Mapped[int] = mapped_column(index=True)
    issuer_nickname: Mapped[str] = mapped_column()
    amount: Mapped[int] = mapped_column()
    trigger_text: Mapped[str] = mapped_column()
    target_role: Mapped[Optional[str]] = mapped_column(nullable=True)
    ascii_target_role: Mapped[Optional[str]] = mapped_column(nullable=True)
    records: Mapped[list["MassDiceBanRecord"]] = relationship(back_populates="entry")


class MassDiceBanRecord(Base):
    __tablename__ = "mass_dice_ban_record"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column()
    user_nickname: Mapped[str] = mapped_column()
    message: Mapped[str] = mapped_column(server_default="")
    entry_id: Mapped[int] = mapped_column(ForeignKey("mass_dice_entry.id"))
    entry: Mapped["MassDiceEntry"] = relationship(back_populates="records")


class VoteBanEntry(Base):
    __tablename__ = "voteban_entry"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    target_user_id: Mapped[int]
    target_nickname: Mapped[str]
    issuer_user_id: Mapped[int]
    issuer_nickname: Mapped[str]
    votes_needed: Mapped[int]

    __table_args__ = (CheckConstraint("votes_needed > 0"),)
