from pydantic import BaseSettings

class Settings(BaseSettings):
    aws_region: str = "us-east-1"
    images_table: str = "Images"
    images_bucket: str = "image-service-bucket"
    presign_ttl_seconds: int = 900

    class Config:
        env_prefix = "IMAGE_SERVICE_"
        case_sensitive = False

settings = Settings()
