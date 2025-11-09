import os
import json
import boto3
import pytest
from moto import mock_aws
from fastapi.testclient import TestClient

os.environ["IMAGE_SERVICE_IMAGES_TABLE"] = "Images"
os.environ["IMAGE_SERVICE_IMAGES_BUCKET"] = "test-bucket"
os.environ["IMAGE_SERVICE_AWS_REGION"] = "us-east-1"
os.environ["IMAGE_SERVICE_PRESIGN_TTL_SECONDS"] = "60"

from app.main import app

client = TestClient(app)

@mock_aws
@pytest.fixture(autouse=True)
def aws_setup():
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=os.environ["IMAGE_SERVICE_IMAGES_BUCKET"])

    ddb = boto3.client("dynamodb", region_name="us-east-1")
    ddb.create_table(
        TableName=os.environ["IMAGE_SERVICE_IMAGES_TABLE"],
        AttributeDefinitions=[
            {"AttributeName": "image_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"},
        ],
        KeySchema=[{"AttributeName": "image_id", "KeyType": "HASH"}],
        GlobalSecondaryIndexes=[{
            "IndexName": "GSI1",
            "KeySchema": [
                {"AttributeName": "user_id", "KeyType": "HASH"},
                {"AttributeName": "created_at", "KeyType": "RANGE"},
            ],
            "Projection": {"ProjectionType": "ALL"},
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
        }],
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
    )
    yield

def test_health():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_presign_then_get_and_delete():
    r = client.post("/images/presign", json={
        "user_id": "u1",
        "content_type": "image/jpeg",
        "tags": ["sunset"]
    })
    assert r.status_code == 201
    body = r.json()
    image_id = body["image_id"]
    assert "upload_url" in body

    r = client.get(f"/images/{image_id}")
    assert r.status_code == 200
    assert r.json()["image_id"] == image_id

    r = client.delete(f"/images/{image_id}")
    assert r.status_code == 204

def test_upload_direct_and_list_filters(tmp_path):
    img_path = tmp_path / "a.jpg"
    img_path.write_bytes(b"\xff\xd8\xff\xd9")

    with open(img_path, "rb") as f:
        r = client.post("/images", files={"file": ("a.jpg", f, "image/jpeg")}, data={
            "user_id": "u2",
            "content_type": "image/jpeg",
            "title": "A",
            "tags": "city,night"
        })
    assert r.status_code == 201
    image_id = r.json()["image_id"]

    r = client.get("/images", params={"user_id": "u2"})
    assert r.status_code == 200
    assert len(r.json()["items"]) == 1

    r = client.get("/images", params={"user_id": "u2", "tag": "city"})
    assert r.status_code == 200
    assert len(r.json()["items"]) == 1

    r = client.get(f"/images/{image_id}")
    assert r.status_code == 200
    assert "download_url" in r.json()
