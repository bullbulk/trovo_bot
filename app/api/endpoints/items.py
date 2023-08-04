from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.crud import track

router = APIRouter()



@router.get("/tracks", response_model=List[schemas.Track])
def read_all(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 10000,
) -> Any:
    """
    Retrieve latest tracks.
    """
    return track.get_latest_multi(db, skip=skip, limit=limit)
