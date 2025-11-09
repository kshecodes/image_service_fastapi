from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from boto3.dynamodb.conditions import Key

from ..aws import s3, images_table
from ..models import CreateImageIn, CreatePresignOut, ImageOut, GetImageOut, now_iso
from ..settings import settings
from ..utils import new_ids

router = APIRouter(prefix="/images", tags=["images"])

@router.post("/presign", response_model=CreatePresignOut, status_code=201)
def create_presigned_upload(req: CreateImageIn):
    image_id, object_key = new_ids(req.user_id)
    item = {
        "image_id": image_id,
        "user_id": req.user_id,
        "bucket": settings.images_bucket,
        "object_key": object_key,
        "content_type": req.content_type,
        "title": req.title,
        "description": req.description,
        "tags": req.tags,
        "status": "PENDING",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    images_table().put_item(Item=item)
    url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": settings.images_bucket, "Key": object_key, "ContentType": req.content_type},
        ExpiresIn=settings.presign_ttl_seconds,
    )
    return CreatePresignOut(image_id=image_id, upload_url=url, object_key=object_key, expires_in=settings.presign_ttl_seconds)

@router.post("", status_code=201)
def upload_direct(
    user_id: str = Form(...),
    content_type: str = Form(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    file: UploadFile = File(...),
):
    tags_list = [t.strip() for t in (tags.split(",") if tags else []) if t.strip()]
    image_id, object_key = new_ids(user_id)

    s3.upload_fileobj(
        Fileobj=file.file,
        Bucket=settings.images_bucket,
        Key=object_key,
        ExtraArgs={"ContentType": content_type},
    )

    item = {
        "image_id": image_id,
        "user_id": user_id,
        "bucket": settings.images_bucket,
        "object_key": object_key,
        "content_type": content_type,
        "title": title,
        "description": description,
        "tags": tags_list,
        "status": "AVAILABLE",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    images_table().put_item(Item=item)

    return {"image_id": image_id, "object_key": object_key}

@router.get("", response_model=Dict[str, Any])
def list_images(
    user_id: str = Query(...),
    tag: Optional[str] = Query(None),
    created_from: Optional[str] = Query(None),
    created_to: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    index_name = "GSI1"
    key_cond = Key("user_id").eq(user_id)
    if created_from or created_to:
        if created_from and created_to:
            key_cond = key_cond & Key("created_at").between(created_from, created_to)
        elif created_from:
            key_cond = key_cond & Key("created_at").gte(created_from)
        else:
            key_cond = key_cond & Key("created_at").lte(created_to)

    resp = images_table().query(
        IndexName=index_name,
        KeyConditionExpression=key_cond,
        Limit=limit,
        ScanIndexForward=False,
        ProjectionExpression="#id, user_id, title, tags, created_at",
        ExpressionAttributeNames={"#id": "image_id"},
    )
    items = resp.get("Items", [])
    if tag:
        items = [it for it in items if tag in (it.get("tags") or [])]
    return {"items": items, "next_token": resp.get("LastEvaluatedKey")}

@router.get("/{image_id}", response_model=GetImageOut)
def get_image(image_id: str):
    resp = images_table().get_item(Key={"image_id": image_id})
    item = resp.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Image not found")

    url = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": item["bucket"], "Key": item["object_key"]},
        ExpiresIn=settings.presign_ttl_seconds,
    )
    meta = {
        "content_type": item.get("content_type"),
        "title": item.get("title"),
        "description": item.get("description"),
        "tags": item.get("tags"),
        "created_at": item.get("created_at"),
        "status": item.get("status"),
    }
    return GetImageOut(image_id=image_id, download_url=url, expires_in=settings.presign_ttl_seconds, metadata=meta)

@router.delete("/{image_id}", status_code=204)
def delete_image(image_id: str):
    resp = images_table().get_item(Key={"image_id": image_id})
    item = resp.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Image not found")

    s3.delete_object(Bucket=item["bucket"], Key=item["object_key"])
    images_table().delete_item(Key={"image_id": image_id})
    return JSONResponse(status_code=204, content=None)
