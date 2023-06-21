from typing import Any

import jwt
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette import status

from app import crud
from app import models
from app import schemas
from app.api import deps
from app.config import settings
from app.core import security
from app.core.security import get_password_hash
from app.schemas import TokenScope
from app.utils import (
    verify_password_reset_token,
)

router = APIRouter()


@router.post("/login/", response_model=schemas.TokenPair)
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests with password
    """
    user = crud.user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not crud.user.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")

    return {
        "access_token": security.create_access_token(user.id),
        "refresh_token": security.create_refresh_token(user.id),
        "token_type": "bearer",
    }


@router.post("/refresh/", response_model=schemas.TokenPair)
def refresh(refresh_token: str, db: Session = Depends(deps.get_db)) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests with refresh token
    """
    try:
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (jwt.PyJWTError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        ) from e

    if token_data.scope.value != TokenScope.REFRESH.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    if user := crud.user.get(db, id_=token_data.sub):
        return {
            "access_token": security.create_access_token(user.id),
            "refresh_token": security.create_refresh_token(user.id),
            "token_type": "bearer",
        }
    else:
        raise HTTPException(status_code=404, detail="User not found")


@router.post("/login/test-token", response_model=schemas.User)
def test_token(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/reset-password/", response_model=schemas.Msg)
def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Reset password
    """
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = crud.user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    elif not crud.user.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")
    password = get_password_hash(new_password)
    user.password = password
    db.add(user)
    db.commit()
    return {"msg": "Password updated successfully"}
