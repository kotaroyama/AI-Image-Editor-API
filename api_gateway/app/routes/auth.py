from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.auth import create_access_token, hash_password, verify_password
from app.schemas import Token, UserCreate
from shared.database import get_session
from shared.models import User

router = APIRouter(
    prefix="",
    tags=["Auth"],
)

@router.post("/register")
async def register(
    user_data: UserCreate,
    session: Annotated[Session, Depends(get_session)],
):
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
    )
    
    session.add(user)

    try:
        session.commit()
        session.refresh(user)
    except IntegrityError as e:
        session.rollback()

        raise HTTPException (
            status_code=400,
            detail="Username already exists",
        )
    
    return user

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)],
):
    user = session.exec(
        select(User).where(User.username == form_data.username)
    ).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token({"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")