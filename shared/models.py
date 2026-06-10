from datetime import datetime, timezone
import uuid

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(max_length=100, unique=True, index=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Photo(SQLModel, table=True):
    __tablename__ = "photos"

    # id: int | None = Field(default=None, primary_key=True)
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False
    )
    owner_id: int = Field(foreign_key="users.id")
    original_filename: str = Field(max_length=255)
    storage_key: str = Field(unique=True, index=True)
    content_type: str = Field(max_length=100)
    file_size: int = Field(ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EditJob(SQLModel, table=True):
    __name__ = "edit_jobs"

    # id: int | None = Field(default=None, primary_key=True)
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False
    )
    owner_id: int = Field(foreign_key="users.id")
    photo_id: uuid.UUID = Field(foreign_key="photos.id")
    operation: str
    status: str
    result_storage_key: str | None = None
    error_message: str | None = None
    created_at:  datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at:  datetime = Field(default_factory=lambda: datetime.now(timezone.utc))