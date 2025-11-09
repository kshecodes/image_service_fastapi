# Image Service (FastAPI)
### Author: Keerthi Sanal

FastAPI service that mirrors the serverless design:
- **POST /images/presign** → returns S3 pre-signed PUT URL + writes metadata (status=PENDING)
- **POST /images** (multipart) → uploads file to S3 via server and writes metadata (status=AVAILABLE)
- **GET /images** → list with filters (`user_id`, `tag`, `created_at` range)
- **GET /images/{image_id}** → returns pre-signed GET URL + metadata
- **DELETE /images/{image_id}** → deletes S3 object + metadata

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export IMAGE_SERVICE_IMAGES_TABLE=Images
export IMAGE_SERVICE_IMAGES_BUCKET=test-bucket
uvicorn app.main:app --reload
# Open http://localhost:8000/docs
```

> For local tests we use `moto` to mock AWS.

## Tests

```bash
pytest -q
```

## Environment variables

- `IMAGE_SERVICE_AWS_REGION` (default `us-east-1`)
- `IMAGE_SERVICE_IMAGES_TABLE` (default `Images`)
- `IMAGE_SERVICE_IMAGES_BUCKET` (default `image-service-bucket`)
- `IMAGE_SERVICE_PRESIGN_TTL_SECONDS` (default `900`)

## Docker

```bash
docker build -t image-service .
docker run -p 8000:8000   -e IMAGE_SERVICE_IMAGES_TABLE=Images   -e IMAGE_SERVICE_IMAGES_BUCKET=test-bucket   image-service
```

## DynamoDB & S3 (prod)

Provision a real DynamoDB table with PK `image_id` and GSI1 (`user_id`, `created_at`), and an S3 bucket.
Use AWS credentials in the environment or default profile for boto3.
