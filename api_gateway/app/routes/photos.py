import os
from pathlib import Path
from typing import Annotated
import uuid

from botocore.exceptions import ClientError
from celery import Celery
from dotenv import load_dotenv, find_dotenv
from fastapi import APIRouter, Depends, File, HTTPException, Response, status, UploadFile
from sqlmodel import Session, select

from app.auth import get_current_user
from app.services.s3 import s3_client, get_presigned_url_photo, EDIT_BUCKET, UPLOAD_BUCKET
from app.schemas import EditJobRequest, EditJobResponse, PhotoRead, PhotoUploadResponse
from shared.database import get_session
from shared.models import EditJob, Photo, User

load_dotenv(find_dotenv())

router = APIRouter(
    prefix="/me/photos",
    tags=["Photos"],
)

CELERY_BROKER = os.getenv("REDIS_URL")
celery_client = Celery("image_tasks", broker=CELERY_BROKER, backend=CELERY_BROKER)

@router.get("", response_model=list[PhotoRead])
async def get_uploaded_photos(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[PhotoRead]:
    photos = session.exec(select(Photo).where(Photo.owner_id == current_user.id))

    if not photos:
        raise HTTPException(status_code=404, detail="No uploaded photos found")
    
    photo_response = []

    for photo in photos:
        url = get_presigned_url_photo(photo)
        photo_response.append(
            PhotoRead(
                id=photo.id,
                original_filename=photo.original_filename,
                url=url,
            )
        )

    return photo_response

@router.get("/{photo_id}", response_model=PhotoRead)
async def get_uploaded_photo(
    photo_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> PhotoRead:
    photo = session.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    url = get_presigned_url_photo(photo)

    return PhotoRead(
        id=photo.id,
        original_filename=photo.original_filename,
        url=url,
    )

@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    photo_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    # Retrieve the photo from the database
    photo = session.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    filename = photo.original_filename
    
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

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/upload")
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

@router.post("/edit", response_model=EditJobResponse)
async def edit_image_request(
    current_user: Annotated[User, Depends(get_current_user)],
    request: EditJobRequest,
    session: Annotated[Session, Depends(get_session)],
):
    user_id = current_user.id
    image_id = request.image_id
    action = request.action
    file_extension = request.file_extension

    filename = f"{image_id}.{file_extension}"
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
        photo_id=image_id,
        operation=action,
        status="PENDING"
    )

    # Send the job to the worker queue
    session.add(new_job)
    session.commit()
    if action == "grayscale":
        celery_client.send_task(
            "tasks.grayscale_image",
            args=[
                job_id,
                image_id,
                user_id,
                action,
                file_extension,
            ],
            queue="default_ops",
        )
    elif action == "rembg":
        celery_client.send_task(
            "tasks.remove_background",
            args=[
                job_id,
                image_id,
                user_id,
                action,
                file_extension,
            ],
            queue="heavy_ai",
        )
    elif action == "yolo":
        celery_client.send_task(
            "tasks.detect_objects",
            args=[
                job_id,
                image_id,
                user_id,
                action,
                file_extension,
            ],
            queue="vision_ai",
        )
    else:
        raise HTTPException(status_code=422, detail="Action not supported")
    
    job_status = str(session.exec(select(EditJob.status).where(EditJob.id == job_id)).first())
    original_filename = str(session.exec(select(Photo.original_filename).where(Photo.id == image_id)).first())

    session.close()
    
    return EditJobResponse(
        image_id=image_id,
        original_filename=original_filename,
        job_id=job_id,
        action=action,
        status=job_status,
    )