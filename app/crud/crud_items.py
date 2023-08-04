from sqlalchemy.orm import Session

from app import models
from app.models import MassDiceEntry, Track
from .base import CRUDBase, CreateSchemaType, UpdateSchemaType

class CRUDTrack(
    CRUDBase[models.MassDiceBanRecord, CreateSchemaType, UpdateSchemaType]
):
    def get_latest_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[Track]:
        return db.query(self.model).order_by(self.model.date_created.desc()).offset(skip).limit(limit).all()




track = CRUDTrack(Track)
