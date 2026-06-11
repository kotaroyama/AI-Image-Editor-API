import uuid

from pydantic import BaseModel
from sqlmodel import SQLModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserCreate(SQLModel):
    username: str
    email: str
    password: str


class UserRead(SQLModel):
    id: int
    username: str
    email: str


class EditRequest(BaseModel):
    image_id: uuid.UUID
    file_extension: str = "jpg"
    action: str
    width: int | None = None
    height: int | None = None


class PhotoUploadResponse(BaseModel):
    image_id: uuid.UUID
    storage_key: str
    original_filename: str
    status: str