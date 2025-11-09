import boto3
from .settings import settings

_session = boto3.session.Session(region_name=settings.aws_region)
s3 = _session.client("s3")
ddb_res = _session.resource("dynamodb")

def images_table():
    return ddb_res.Table(settings.images_table)
