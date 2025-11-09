from fastapi import FastAPI
from .routes.images import router as images_router

app = FastAPI(
    title="Image Service (FastAPI)",
    version="1.0.0",
    description="FastAPI service for image upload/list/get/delete using S3 + DynamoDB",
)

app.include_router(images_router)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
