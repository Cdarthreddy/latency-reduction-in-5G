# utils/manifest.py
import json, os, socket
from datetime import datetime
from config import RUN_ID, AWS_REGION, S3_BUCKET, get_s3_prefix

def create_manifest(sim_type: str, episodes: int, tasks: int, avg_latency: float) -> dict:
    """Builds a manifest metadata dictionary."""
    manifest = {
        "run_id": RUN_ID,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "simulator": sim_type,
        "episodes": episodes,
        "tasks": tasks,
        "avg_latency_ms": round(avg_latency, 3),
        "region": AWS_REGION,
        "s3_bucket": S3_BUCKET,
        "s3_prefix": get_s3_prefix(),
        "host": socket.gethostname(),
    }
    return manifest

def save_manifest_local(manifest: dict, data_dir="data") -> str:
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, "manifest.json")
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
    return path
