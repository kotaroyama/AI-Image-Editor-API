from datetime import datetime
from typing import Dict, Any, List
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


class EditJobBase(BaseModel):
    image_id: uuid.UUID
    action: str

class EditJobRequest(EditJobBase):
    file_extension: str = "jpg"

class EditJobResponse(EditJobBase):
    job_id: uuid.UUID
    original_filename: str
    status: str


class PhotoUploadResponse(BaseModel):
    image_id: uuid.UUID
    storage_key: str
    original_filename: str
    status: str

class PhotoRead(BaseModel):
    id: uuid.UUID
    storage_key: str
    original_filename: str

class JobRead(BaseModel):
    id: uuid.UUID
    image_id: uuid.UUID
    original_filename: str
    action: str
    status: str

    # Timing metrics
    created_at: datetime
    updated_at: datetime | None = None

    # Dynamic Data Results
    url: str | None = None
    detected_labels: List[Dict[str, Any]] | None = None
    error_message: str | None = None

    class Config:
        from_attributes = True