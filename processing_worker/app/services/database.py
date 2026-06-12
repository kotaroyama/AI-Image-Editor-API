from shared.database import get_session
from shared.models import EditJob, Photo

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

def insert_detected_objects(photo_id, detected_objects):
    session_gen = get_session()
    session = next(session_gen)

    try:
        photo = session.get(Photo, photo_id)

        if not photo:
            raise ValueError("Photo not found")

        photo.detected_labels = detected_objects

        session.add(photo)
        session.commit()
        session.refresh(photo)
    except Exception as e:
        session.rollback()
        raise
    finally:
        session_gen.close()