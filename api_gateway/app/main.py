import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from PIL import Image

from schemas import EditRequest

app = FastAPI()

s3_client = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="REMOVED_ACCESS_KEY_FOR_RUSTFS",
    aws_secret_access_key="REMOVED_SECRET_KEY_FOR_RUSTFT",
    config=Config(signature_version='s3v4'),  # Ensures modern AWS signature compatibility
    region_name="ap-east-2",
)

# Create buckets buckets for storing and editing images
UPLOAD_BUCKET = "uploads"
EDIT_BUCKET = "edits"
s3_client.create_bucket(Bucket=UPLOAD_BUCKET)
s3_client.create_bucket(Bucket=EDIT_BUCKET)

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    # Ensure the file is an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Generate a unique ID for the image
    image_id = str(uuid.uuid4())
    file_extension = file.filename.split(".")[-1]
    object_key = f"{image_id}.{file_extension}"

    s3_client.upload_fileobj(file.file, UPLOAD_BUCKET, object_key)

    return {"image_id": image_id}

def edit_image(image_id, action, params={}):
    source_key = f"{image_id}"
    output_key = f"edited_{action}_{image_id}"

    local_input = f"/tmp/input_{source_key}"
    local_output = f"/tmp/output_{output_key}"
    
    # if not os.path.exists(input_path):
    #     raise HTTPException(status_code=404, detail="Image not found")
    try:
        s3_client.download_file(UPLOAD_BUCKET, source_key, local_input)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code in ["404", "NoSuchKey"]:
            print(f"Background Error: Image {image_id} not found.")
        else:
            print(f"System Storage Error: {e}")

    with Image.open(local_input) as img:
        if action == "grayscale":
            processed_img = img.convert("L")
        elif action == "resize":
            w, h = params.get("width"), params.get("height")
            if w == 0 or h == 0:
                raise HTTPException(status_code=400, detail="Width or height cannot be 0")
            processed_img = img.resize((w, h), Image.Resampling.LANCZOS)
        else:
            raise HTTPException(status_code=400, detail="Unsupported action")
        processed_img.save(local_output)
    
    s3_client.upload_file(local_output, EDIT_BUCKET, output_key)

@app.post("/edit")
async def edit_image_request(request: EditRequest, background_tasks: BackgroundTasks, width: int = 0, height: int = 0):
    try:
        s3_client.head_object(Bucket=UPLOAD_BUCKET, Key=f"{request.image_id}")
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ["404", "NoSuchKey"]:
            raise HTTPException(status_code=404, detail="Image not found in storage.")

    
    sizes = {"width": width, "height": height}
    background_tasks.add_task(edit_image, request.image_id, request.action, params=sizes)
    return {"message": "Editing in progress in the background"}