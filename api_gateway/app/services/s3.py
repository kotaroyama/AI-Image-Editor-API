import os

import boto3
from botocore.config import Config

# Create buckets buckets for storing and editing images
EDIT_BUCKET = os.getenv("EDIT_BUCKET")
UPLOAD_BUCKET = os.getenv("UPLOAD_BUCKET")

s3_client = boto3.client(
    "s3",
    region_name="ap-east-2",
    endpoint_url="https://s3.ap-east-2.amazonaws.com",
    config=Config(signature_version='s3v4')
)

def get_presigned_url_job(job):
    presigned_url = None
    if job.status == "COMPLETED" and job.result_storage_key:
        storage_key = job.result_storage_key
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": EDIT_BUCKET,
                "Key": storage_key 
            },
            ExpiresIn=6000
        )
    return presigned_url

def get_presigned_url_photo(photo):
    storage_key = photo.storage_key
    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": UPLOAD_BUCKET,
            "Key": storage_key
        },
        ExpiresIn=6000,
    )
    return presigned_url
