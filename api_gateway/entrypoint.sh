#!/bin/bash
# Stop execution immediately if any command fails
set -e

echo "--------------------------------------------------------"
echo "Injecting production runtime variables from AWS SSM..."
echo "--------------------------------------------------------"

# 1. Fetch parameters using the container's built-in AWS CLI tool
export DATABASE_URL=$(aws ssm get-parameter --name "/prod/photo-editor/DATABASE_URL" --with-decryption --query "Parameter.Value" --output text --region ap-east-2)
export REDIS_URL=$(aws ssm get-parameter --name "/prod/photo-editor/REDIS_URL" --query "Parameter.Value" --output text --region ap-east-2)
export UPLOAD_BUCKET=$(aws ssm get-parameter --name "/prod/photo-editor/UPLOAD_BUCKET" --query "Parameter.Value" --output text --region ap-east-2)
export EDIT_BUCKET=$(aws ssm get-parameter --name "/prod/photo-editor/EDIT_BUCKET" --query "Parameter.Value" --output text --region ap-east-2)

export JWT_SECRET_KEY=$(aws ssm get-parameter --name "/prod/photo-editor/JWT_SECRET_KEY" --with-decryption --query "Parameter.Value" --output text --region ap-east-2)

# 2. Tell Python exactly where to look so it maps 'shared' and 'app' flawlessly
export PYTHONPATH=/app:/app/api_gateway

echo $REDIS_URL

echo "Variables successfully injected. Starting FastAPI Gateway..."
echo "--------------------------------------------------------"

# 3. Handoff execution to Uvicorn pointing directly to the application entry module
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
