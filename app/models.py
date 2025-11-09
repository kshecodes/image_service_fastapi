from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

class CreateImageIn(BaseModel):
    user_id: str
    content_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class ImageOut(BaseModel):
    image_id: str
    user_id: str
    title: Optional[str] = None
    tags: List[str] = []
    created_at: str

class CreatePresignOut(BaseModel):
    image_id: str
    upload_url: str
    object_key: str
    expires_in: int

class GetImageOut(BaseModel):
    image_id: str
    download_url: str
    expires_in: int
    metadata: dict
