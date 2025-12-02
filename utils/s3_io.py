# utils/s3_io.py
import boto3, os
from botocore.exceptions import ClientError
from config import AWS_REGION, S3_BUCKET, RUN_ID

s3 = boto3.client("s3", region_name=AWS_REGION)

def _prefix():
    # Folder per run
    return f"runs/{RUN_ID}"

def upload_file(local_path: str, key_prefix: str | None = None) -> str:
    if not os.path.exists(local_path):
        print(f"[WARN] Missing file: {local_path}")
        return ""
    prefix = key_prefix or _prefix()
    key = f"{prefix}/{os.path.basename(local_path)}"
    try:
        s3.upload_file(local_path, S3_BUCKET, key)
        url = f"s3://{S3_BUCKET}/{key}"
        print(f"[OK] Uploaded -> {url}")
        return url
    except ClientError as e:
        print(f"[ERROR] S3 upload failed: {e}")
        return ""
