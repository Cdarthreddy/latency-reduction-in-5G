# config.py
import os
from datetime import datetime, timezone

# --------------------------------------------------------------------
# Core configuration for AWS + data paths
# --------------------------------------------------------------------
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET  = os.getenv("S3_BUCKET", "latency-results-project")  # ← use your bucket
DATA_DIR   = os.getenv("DATA_DIR", "data")

# Generate unique run ID (ISO timestamp)
RUN_ID = os.getenv("RUN_ID", f"run-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")

# --------------------------------------------------------------------
# Helper to get S3 prefix (used by main_remote.py)
# --------------------------------------------------------------------
def get_s3_prefix() -> str:
    """
    Returns the S3 folder prefix for the current run.
    e.g., 'runs/run-20251027T131840Z'
    """
    return f"runs/{RUN_ID}"

# --------------------------------------------------------------------
# Show config summary when loaded
# --------------------------------------------------------------------
print(f"[config] Using region={AWS_REGION}, bucket={S3_BUCKET}, run={RUN_ID}")
