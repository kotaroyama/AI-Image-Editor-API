FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for image processing / psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    libglib2.0-0 \
    libxcb1 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libsm6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y opencv-python opencv-contrib-python || true && \
    pip install --no-cache-dir --force-reinstall opencv-python-headless

# Pre-download the rembg model weights so container starts instantly
RUN python -c "from rembg import new_session; new_session('u2net')"

COPY . .

# Command to start the Celery worker process listening to the queue
CMD ["celery", "-A", "app.tasks.celery_app", "worker", "--loglevel=info"]