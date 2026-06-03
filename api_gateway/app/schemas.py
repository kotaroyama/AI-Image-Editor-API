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
    image_id: str
    file_extension: str
    action: str


class PhotoUploadResponse(BaseModel):
    image_id: int
    storage_key: str
    original_filename: str
    status: str