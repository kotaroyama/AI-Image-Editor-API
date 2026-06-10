from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import Annotated
import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from celery import Celery
from dotenv import load_dotenv, find_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database import create_db_and_tables, get_session
from app.models import EditJob, Photo, User
from app.schemas import EditRequest, PhotoUploadResponse, Token, UserCreate, UserRead

load_dotenv(find_dotenv())

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

CELERY_BROKER = os.getenv("REDIS_URL")
celery_client = Celery("image_tasks", broker=CELERY_BROKER, backend=CELERY_BROKER)

s3_client = boto3.client(
    "s3",
    endpoint_url=os.environ.get("RUSTFS_ENDPOINT"),
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version='s3v4'),  # Ensures modern AWS signature compatibility
    region_name="ap-east-2",
)

# Create buckets buckets for storing and editing images
UPLOAD_BUCKET = "uploads"
EDIT_BUCKET = "edits"
s3_client.create_bucket(Bucket=UPLOAD_BUCKET)
s3_client.create_bucket(Bucket=EDIT_BUCKET)

@app.post("/upload")
async def upload_image(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    file: UploadFile = File(...),
) -> PhotoUploadResponse:
    # Ensure the file is an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Generate a unique ID for the image
    user_id = current_user.id
    image_id = str(uuid.uuid4())
    original_filename = file.filename
    file_extension = Path(file.filename).suffix.lower().lstrip(".")
    object_key = f"users/{user_id}/photos/{image_id}.{file_extension}"

    # Insert a row to the photos table in the database
    db_photo = Photo(
        id=image_id,
        owner_id=user_id,
        original_filename=original_filename,
        storage_key=object_key,
        content_type=file.content_type,
        file_size=file.size,
    )
    session.add(db_photo)
    session.commit()
    session.refresh(db_photo)

    # Upload the image to S3 bucket
    s3_client.upload_fileobj(file.file, UPLOAD_BUCKET, object_key)

    return PhotoUploadResponse(
        image_id=db_photo.id,
        storage_key=object_key,
        original_filename=original_filename,
        status="uploaded",
    )

@app.post("/edit")
async def edit_image_request(
    current_user: Annotated[User, Depends(get_current_user)],
    request: EditRequest,
    session: Annotated[Session, Depends(get_session)],
):
    user_id = current_user.id
    filename = f"{request.image_id}.{request.file_extension}"
    object_key = f"users/{user_id}/photos/{filename}"

    try:
        s3_client.head_object(Bucket=UPLOAD_BUCKET, Key=object_key)
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ["404", "NoSuchKey"]:
            raise HTTPException(status_code=404, detail="Image not found in storage.")

    job_id = str(uuid.uuid4())

    # Add the job to the SQL database
    new_job = EditJob(
        id=job_id,
        owner_id=user_id,
        photo_id=request.image_id,
        operation=request.action,
        status="PENDING"
    )
    session.add(new_job)
    session.commit()

    # Send the job to the worker queue
    celery_client.send_task(
        "tasks.process_image",
        args=[
            job_id,
            request.image_id,
            user_id, request.action,
            request.file_extension,
            { "width": request.width, "height": request.height },
        ]
    )
    
    return {"job_id": job_id, "status": "PENDING"}

@app.post("/register")
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

@app.post("/token")
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