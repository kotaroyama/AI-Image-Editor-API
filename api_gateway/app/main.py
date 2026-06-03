from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from PIL import Image
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from auth import create_access_token, get_current_user, hash_password, verify_password
from database import create_db_and_tables, get_session
from models import User, Photo
from schemas import EditRequest, PhotoUploadResponse, Token, UserCreate, UserRead

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

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

def edit_image(filename, user_id, action, params={}):
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
async def edit_image_request(
    current_user: Annotated[User, Depends(get_current_user)],
    request: EditRequest,
    background_tasks: BackgroundTasks,
    width: int = 0,
    height: int = 0
):
    user_id = current_user.id
    filename = f"{request.image_id}.{request.file_extension}"
    object_key = f"users/{user_id}/photos/{filename}"

    try:
        s3_client.head_object(Bucket=UPLOAD_BUCKET, Key=object_key)
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ["404", "NoSuchKey"]:
            raise HTTPException(status_code=404, detail="Image not found in storage.")

    sizes = {"width": width, "height": height}
    background_tasks.add_task(edit_image, filename, user_id, request.action, params=sizes)
    return {"message": "Editing in progress in the background"}

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