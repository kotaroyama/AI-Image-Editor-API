import os

from celery import Celery

from app.services.database import update_job_status
from app.services.storage import download_image, upload_image, remove_remaining_files
from app.editors.basic_ops import grayscale_process_image
from app.editors.ai_ops import rembg_process_image, yolo_process_image

CELERY_BROKER = os.getenv("REDIS_URL")
celery_app = Celery("image_tasks", broker=CELERY_BROKER, backend=CELERY_BROKER)

@celery_app.task(name="tasks.grayscale_image", queue="default_ops")
def grayscale_image(
    job_id: str,
    image_id: str,
    user_id: str,
    action: str,
    ext: str,
):
    print(f"Starting job {job_id} for photo {image_id} (Action: {action})")

    update_job_status(job_id, "PROCESSING")    

    # Download the image from RustFS
    filename = f"{image_id}.{ext}"
    source_key = f"users/{user_id}/photos/{filename}"
    output_key = f"users/{user_id}/photos/edited_{action}_{filename}"

    local_input = f"/tmp/input_{filename}"
    local_output = f"/tmp/output_{filename}"

    download_image(source_key, local_input, filename)

    # Apply the edit logic
    try:
        if action == "grayscale":
            grayscale_process_image(local_input, local_output)
        else:
            raise ValueError(f"Unknown action: {action}")
        
        # Upload the edited image to S3 storage
        upload_image(local_output, output_key)

        # Update the database job to "SUCCESS" and store result_storage_key
        update_job_status(job_id, "COMPLETED", result_storage_key=output_key)

        print(f"Job {job_id} successfully completed!")
    except Exception as e:
        print(f"Job {job_id} failed: {str(e)}")
        update_job_status(job_id, "FAILED", error_message=str(e))
        remove_remaining_files(local_input, local_output)
        raise

@celery_app.task(name="tasks.remove_background", queue="heavy_ai")
def remove_background(
    job_id: str,
    image_id: str,
    user_id: str,
    action: str,
    ext: str,
):
    print(f"Starting job {job_id} for photo {image_id} (Action: {action})")

    update_job_status(job_id, "PROCESSING")    

    # Download the image from RustFS
    filename = f"{image_id}.{ext}"
    source_key = f"users/{user_id}/photos/{filename}"
    output_key = f"users/{user_id}/photos/edited_{action}_{image_id}.png"

    local_input = f"/tmp/input_{filename}"
    local_output = f"/tmp/output_{image_id}.png"
    
    download_image(source_key, local_input, filename)

    # Apply the edit logic
    try:
        if action == "rembg":
            rembg_process_image(local_input, local_output)
        else:
            raise ValueError(f"Unknown action: {action}")

        # Upload the edited image to S3 storage
        upload_image(local_output, output_key)

        # Update the database job to "SUCCESS" and store result_storage_key
        update_job_status(job_id, "COMPLETED", result_storage_key=output_key)

        print(f"Job {job_id} successfully completed!")
    except Exception as e:
        print(f"Job {job_id} failed: {str(e)}")
        update_job_status(job_id, "FAILED", error_message=str(e))
        remove_remaining_files(local_input, local_output)
        raise

@celery_app.task(name="tasks.detect_objects", queue="vision_ai")
def detect_objects(
    job_id: str,
    image_id: str,
    user_id: str,
    action: str,
    ext: str,
):
    print(f"Starting job {job_id} for photo {image_id} (Action: {action})")

    update_job_status(job_id, "PROCESSING")    

    # Download the image from RustFS
    filename = f"{image_id}.{ext}"
    source_key = f"users/{user_id}/photos/{filename}"
    output_key = f"users/{user_id}/photos/edited_{action}_{image_id}.png"

    local_input = f"/tmp/input_{filename}"
    local_output = f"/tmp/output_{filename}"
    
    download_image(source_key, local_input, filename)

    # Apply the edit logic
    try:
        if action == "yolo":
            results = yolo_process_image(local_input, local_output)
        else:
            raise ValueError(f"Unknown action: {action}")

        # Upload the edited image to S3 storage
        upload_image(local_output, output_key)

        # Update the database job to "SUCCESS" and store result_storage_key
        update_job_status(job_id, "COMPLETED")
    
        print(f"Job {job_id} successfully completed!")
    except Exception as e:
        print(f"Job {job_id} failed: {str(e)}")
        update_job_status(job_id, "FAILED", error_message=str(e))
        remove_remaining_files(local_input, local_output)
        raise