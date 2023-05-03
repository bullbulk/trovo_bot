from sqlalchemy.orm import Session

from app import models
from app.models import DiceAmount, MassDiceEntry
from .base import CRUDBase, CreateSchemaType, UpdateSchemaType


class CRUDDiceAmount(CRUDBase[models.DiceAmount, CreateSchemaType, UpdateSchemaType]):
    def subtract(
        self,
        db: Session,
        *,
        db_obj: DiceAmount,
        amount: int,
    ) -> DiceAmount:
        return super().update(db, db_obj=db_obj, obj_in={"amount": amount})

    def get_by_owner(self, db: Session, *, user_id: int) -> DiceAmount | None:
        return db.query(self.model).filter(DiceAmount.user_id == user_id).first()


class CRUDMassDiceEntry(
    CRUDBase[models.MassDiceEntry, CreateSchemaType, UpdateSchemaType]
):
    def get_active_multi(self, db: Session) -> list[models.MassDiceEntry]:
        return db.query(self.model).filter(MassDiceEntry.amount > 0).all()

    def subtract(
        self,
        db: Session,
        *,
        db_obj: MassDiceEntry,
        amount: int,
    ) -> MassDiceEntry:
        return super().update(db, db_obj=db_obj, obj_in={"amount": amount})


class CRUDMassDiceBanRecord(
    CRUDBase[models.MassDiceBanRecord, CreateSchemaType, UpdateSchemaType]
):
    pass


dice_amount = CRUDDiceAmount(DiceAmount)
mass_dice_entry = CRUDMassDiceEntry(models.MassDiceEntry)
mass_ban_record = CRUDMassDiceBanRecord(models.MassDiceEntry)
