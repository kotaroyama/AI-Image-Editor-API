from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, photos, jobs
from app.services.s3 import s3_client, EDIT_BUCKET, UPLOAD_BUCKET

from shared.database import create_db_and_tables

# Create Database
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(photos.router)
app.include_router(jobs.router)

# Create buckets buckets for storing and editing images
s3_client.create_bucket(Bucket=UPLOAD_BUCKET)
s3_client.create_bucket(Bucket=EDIT_BUCKET)