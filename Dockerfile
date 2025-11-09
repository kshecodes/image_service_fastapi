FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV IMAGE_SERVICE_AWS_REGION=us-east-1     IMAGE_SERVICE_IMAGES_TABLE=Images     IMAGE_SERVICE_IMAGES_BUCKET=image-service-bucket     IMAGE_SERVICE_PRESIGN_TTL_SECONDS=900

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
