FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y \
    awscli \
    curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY api_gateway/requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . .
RUN chmod +x /app/api_gateway/entrypoint.sh
CMD ["uvicorn", "api_gateway.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
