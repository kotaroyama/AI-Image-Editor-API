import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from celery import Celery
from PIL import Image
from rembg import remove, new_session

from app.database import get_session
from app.models import EditJob

s3_client = boto3.client(
    "s3",
    endpoint_url=os.environ.get("RUSTFS_ENDPOINT"),
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version='s3v4'),  # Ensures modern AWS signature compatibility
    region_name="ap-east-2",
)

UPLOAD_BUCKET = "uploads"
EDIT_BUCKET = "edits"

CELERY_BROKER = os.getenv("REDIS_URL")
celery_app = Celery("image_tasks", broker=CELERY_BROKER, backend=CELERY_BROKER)

print("Loading rembg AI model into memory")
AI_SESSION = new_session("u2net")

def update_job_status(
    job_id: str,
    status: str,
    result_storage_key: str | None = None,
    error_message: str | None = None,
):
    session_gen = get_session()
    session = next(session_gen) 

    try:
        edit_job = session.get(EditJob, job_id)

        if not edit_job:
            raise ValueError("Job not found")        
        
        edit_job.status = status.upper()
        if result_storage_key:
            edit_job.result_storage_key = result_storage_key
        if error_message:
            edit_job.error_message = error_message

        session.add(edit_job)
        session.commit()
        session.refresh(edit_job)
    except Exception as e:
        session.rollback()
        raise
    finally:
        session_gen.close()

@celery_app.task(name="tasks.process_image")
def process_image(
    job_id: str,
    image_id: str,
    user_id: str,
    action: str,
    ext: str,
    params={}
):
    print(f"Starting job {job_id} for photo {image_id} (Action: {action})")

    update_job_status(job_id, "PROCESSING")    

    # Download the image from RustFS
    filename = f"{image_id}.{ext}"
    source_key = f"users/{user_id}/photos/{filename}"
    output_key = f"users/{user_id}/photos/edited_{action}_{filename}"

    local_input = f"/tmp/input_{filename}"
    local_output = f"/tmp/output_{filename}"
    
    try:
        s3_client.download_file(UPLOAD_BUCKET, source_key, local_input)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code in ["404", "NoSuchKey"]:
            print(f"Background Error: Image {filename} not found.")
        else:
            print(f"System Storage Error: {e}")

    # Apply the edit logic
    try:
        with Image.open(local_input) as img:
            if action == "grayscale":
                processed_img = img.convert("L")
            elif action == "resize":
                w, h = params.get("width"), params.get("height")
                if w == 0 or h == 0:
                    raise ValueError("Width and height cannot be empty for resizing")
                processed_img = img.resize((w, h), Image.Resampling.LANCZOS)
            elif action == "rembg":
                processed_img = remove(img, session=AI_SESSION)
            else:
                raise ValueError(f"Unknown action: {action}")
            processed_img.save(local_output)
        s3_client.upload_file(local_output, EDIT_BUCKET, output_key)

        # Update the database job to "SUCCESS" and store result_storage_key
        update_job_status(job_id, "COMPLETED", result_storage_key=output_key)
        print(f"Job {job_id} successfully completed!")
    except Exception as e:
        print(f"Job {job_id} failed: {str(e)}")
        update_job_status(job_id, "FAILED", error_message=str(e))

        if os.path.exists(local_input): os.remove(local_input)
        if os.path.exists(local_output): os.remove(local_output)
        
        raise