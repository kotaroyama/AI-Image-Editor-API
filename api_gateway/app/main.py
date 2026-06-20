from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routes import auth, photos, jobs
from app.services.s3 import s3_client, EDIT_BUCKET, UPLOAD_BUCKET

from shared.database import create_db_and_tables

# Create Database
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(photos.router)
app.include_router(jobs.router)
