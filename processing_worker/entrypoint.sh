#!/bin/bash
set -e

echo "--------------------------------------------------------"
echo "Injecting background worker variables from AWS SSM..."
echo "--------------------------------------------------------"

# Fetch environment metrics from your secure cloud configuration path
export DATABASE_URL=$(aws ssm get-parameter --name "/prod/photo-editor/DATABASE_URL" --with-decryption --query "Parameter.Value" --output text --region ap-east-2)
export REDIS_URL=$(aws ssm get-parameter --name "/prod/photo-editor/REDIS_URL" --query "Parameter.Value" --output text --region ap-east-2)
export UPLOAD_BUCKET=$(aws ssm get-parameter --name "/prod/photo-editor/UPLOAD_BUCKET" --query "Parameter.Value" --output text --region ap-east-2)
export EDIT_BUCKET=$(aws ssm get-parameter --name "/prod/photo-editor/EDIT_BUCKET" --query "Parameter.Value" --output text --region ap-east-2)

# Set the path scope so Python unifies 'shared' and 'processing_worker' spaces smoothly
export PYTHONPATH=/app:/app/processing_worker

echo $REDIS_URL
echo $DATABASE_URL

echo "Variables successfully injected. Launching targeted Celery worker daemon..."
echo "--------------------------------------------------------"

# Forward execution straight to the tailored queue arguments passed down from compose
exec "$@"
