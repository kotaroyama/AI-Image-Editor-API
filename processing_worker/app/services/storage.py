import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

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

def download_image(source_key, local_input, filename):
    try:
        s3_client.download_file(UPLOAD_BUCKET, source_key, local_input)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code in ["404", "NoSuchKey"]:
            print(f"Background Error: Image {filename} not found.")
        else:
            print(f"System Storage Error: {e}")

def upload_image(local_output, output_key):
    s3_client.upload_file(local_output, EDIT_BUCKET, output_key)

def remove_remaining_files(local_input, local_output):
    if os.path.exists(local_input): os.remove(local_input)
    if os.path.exists(local_output): os.remove(local_output)
