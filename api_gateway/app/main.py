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
from shared.database import create_db_and_tables, get_session
from shared.models import EditJob, Photo, User
from app.schemas import EditRequest, JobRead, PhotoRead, PhotoUploadResponse, Token, UserCreate

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

@app.get("/me/photos", response_model=list[PhotoRead])
async def get_uploaded_photos(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[Photo]:
    photos = session.exec(select(Photo).where(Photo.owner_id == current_user.id))
    if not photos:
        raise HTTPException(status_code=404, detail="No uploaded photos found")
    return photos

@app.get("/me/photos/{photo_id}", response_model=PhotoRead)
async def get_uploaded_photo(
    photo_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Photo:
    photo = session.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo

@app.get("/me/jobs", response_model=list[JobRead])
async def get_uploaded_photos(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[EditJob]:
    jobs = session.exec(select(EditJob).where(EditJob.owner_id == current_user.id))
    if not jobs:
        raise HTTPException(status_code=404, detail="No edit jobs found")
    
    job_response = []
    for job in jobs:
        presigned_url = None
        if job.status == "COMPLETED" and job.result_storage_key:
            storage_key = job.result_storage_key
            s3_client_public = boto3.client(
                "s3",
                endpoint_url=os.environ.get("RUSTFS_ENDPOINT_PUBLIC"),
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name="ap-east-2",
            )
            presigned_url = s3_client_public.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": EDIT_BUCKET, "Key": storage_key},
                ExpiresIn=6000,
            )
            s3_client_public.close()

        job_response.append(
            JobRead(
                id=job.id,
                image_id=job.photo_id,
                action=job.operation,
                status=job.status,
                created_at=job.created_at,
                updated_at=job.updated_at,
                url=presigned_url,
                error_message=job.error_message
            )
        )
    return job_response

@app.get("/me/jobs/{job_id}", response_model=JobRead)
async def get_job_status(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> EditJob:
    job = session.exec(
        select(EditJob)
        .where(EditJob.id == job_id and EditJob.owner_id == current_user.id)
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Generate the presigned URL dynamically if the task completed
    presigned_url = None
    if job.status == "COMPLETED" and job.result_storage_key:
        storage_key = job.result_storage_key
        s3_client_public = boto3.client(
            "s3",
            endpoint_url=os.environ.get("RUSTFS_ENDPOINT_PUBLIC"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name="ap-east-2",
        )
        presigned_url = s3_client_public.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": EDIT_BUCKET, "Key": storage_key},
            ExpiresIn=6000,
        )
        s3_client_public.close()
    
    # Fetch matched labels if the action is YOLO
    labels = None
    if job.action == "yolo" and job.status == "COMPLETED":
        photo = session.exec(select(Photo).where(Photo.id == job.photo_id)).first()
        labels = photo.detected_labels if photo else None

    return JobRead(
        id=job.id,
        image_id=job.photo_id,
        action=job.operation,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at,
        url=presigned_url,
        detected_labels=labels,
        error_message=job.error_message
    )

@app.delete("/me/photos/{photo_id}")
async def delete_photo(
    photo_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    # Retrieve the photo from the database
    photo = session.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # Gather all the jobs and their keys
    storage_keys = []
    for job in photo.jobs:
        if job.result_storage_key:
            storage_keys.append(job.result_storage_key)
    
    # Delete all files associated with this photo from S3
    # First, delete from the UPLOAD bucket
    s3_client.delete_object(Bucket=UPLOAD_BUCKET, Key=photo.storage_key)

    # Next, delete from the EDIT bucket
    for storage_key in storage_keys:
        s3_client.delete_object(Bucket=EDIT_BUCKET, Key=storage_key)
    
    # Delete the photo from the database
    session.delete(photo)
    session.commit()

    return {"status": f"{photo_id} deleted successfully"}

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

    # Send the job to the worker queue
    if request.action == "grayscale":
        celery_client.send_task(
            "tasks.grayscale_image",
            args=[
                job_id,
                request.image_id,
                user_id, request.action,
                request.file_extension,
            ],
            queue="default_ops",
        )
        session.add(new_job)
        session.commit()
    elif request.action == "rembg":
        celery_client.send_task(
            "tasks.remove_background",
            args=[
                job_id,
                request.image_id,
                user_id, request.action,
                request.file_extension,
            ],
            queue="heavy_ai",
        )
        session.add(new_job)
        session.commit()
    elif request.action == "yolo":
        celery_client.send_task(
            "tasks.detect_objects",
            args=[
                job_id,
                request.image_id,
                user_id, request.action,
                request.file_extension,
            ],
            queue="vision_ai",
        )
        session.add(new_job)
        session.commit()
    else:
        raise HTTPException(status_code=422, detail="Action not supported")
    
    session.close()
    
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