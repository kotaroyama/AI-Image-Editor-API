import os

import boto3
from botocore.config import Config
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Create buckets buckets for storing and editing images
EDIT_BUCKET = os.getenv("EDIT_BUCKET")
UPLOAD_BUCKET = os.getenv("UPLOAD_BUCKET")

s3_client = boto3.client(
    "s3",
    endpoint_url=os.environ.get("RUSTFS_ENDPOINT"),
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version='s3v4'),  # Ensures modern AWS signature compatibility
    region_name="ap-east-2",
)

def get_presigned_url_job(job):
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
    return presigned_url

def get_presigned_url_photo(photo):
    storage_key = photo.storage_key
    s3_client_public = boto3.client(
        "s3",
        endpoint_url=os.environ.get("RUSTFS_ENDPOINT_PUBLIC"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name="ap-east-2",
    )
    presigned_url = s3_client_public.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": UPLOAD_BUCKET, "Key": storage_key},
        ExpiresIn=6000,
    )
    s3_client_public.close()
    return presigned_url