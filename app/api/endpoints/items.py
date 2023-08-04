from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.crud.base import CRUDBase

router = APIRouter()



@router.get("/tracks", response_model=List[schemas.Track])
def read_all(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 10000,
) -> Any:
    """
    Retrieve all tracks.
    """
    return CRUDBase(models.Track).get_multi(db, skip=skip, limit=limit)
