from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.auth import get_current_user
from app.services.s3 import get_presigned_url_job
from app.schemas import JobRead
from shared.database import get_session
from shared.models import EditJob, Photo, User

router = APIRouter(
    prefix="/me/jobs",
    tags=["Jobs"],
)

@router.get("", response_model=list[JobRead])
async def get_uploaded_photos(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[EditJob]:
    jobs = session.exec(select(EditJob).where(EditJob.owner_id == current_user.id))
    if not jobs:
        raise HTTPException(status_code=404, detail="No edit jobs found")
    
    job_response = []
    for job in jobs:
        presigned_url = get_presigned_url_job(job)
        job_response.append(
            JobRead(
                id=job.id,
                image_id=job.photo_id,
                original_filename=job.photo.original_filename,
                action=job.operation,
                status=job.status,
                created_at=job.created_at,
                updated_at=job.updated_at,
                url=presigned_url,
                error_message=job.error_message
            )
        )
    return job_response

@router.get("/{job_id}", response_model=JobRead)
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
    presigned_url = get_presigned_url_job(job)
    
    # Fetch matched labels if the action is YOLO
    labels = None
    if job.operation == "yolo" and job.status == "COMPLETED":
        photo = session.exec(select(Photo).where(Photo.id == job.photo_id)).first()
        labels = photo.detected_labels if photo else None

    return JobRead(
        id=job.id,
        image_id=job.photo_id,
        original_filename=job.photo.original_filename,
        action=job.operation,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at,
        url=presigned_url,
        detected_labels=labels,
        error_message=job.error_message
    )