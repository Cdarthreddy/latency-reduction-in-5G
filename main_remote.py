"""
Remote runner for EC2: executes training + evaluation + uploads artifacts to S3.
Now extended for Week 11:
 - Generates manifest.json (metadata for reproducibility)
 - Uploads all artifacts including manifest to S3
"""

import os
from orchestrator.generate_workloads import WorkloadGenerator
from train_rl import train_and_eval
from utils.s3_io import upload_file
from utils.manifest import create_manifest, save_manifest_local
from config import DATA_DIR, get_s3_prefix

def ensure_workload():
    """Ensures workloads.csv exists before training."""
    workload_file = os.path.join(DATA_DIR, "workloads.csv")
    if not os.path.exists(workload_file):
        print("⚙️ No workloads.csv found → generating new one...")
        WorkloadGenerator(num_tasks=300, poisson_lambda=3.0).generate()
    else:
        print("✅ Workload already present; re-using existing file.")


def main():
    """Main entrypoint for remote orchestration."""
    ensure_workload()

    # Train + evaluate RL orchestrator
    print("🚀 Starting training + evaluation...")
    avg_latency = train_and_eval()  # returns average latency
    prefix = get_s3_prefix()

    # ----------------------------------------------------------------------
    # 1️⃣ Create and save manifest
    # ----------------------------------------------------------------------
    manifest = create_manifest(
        sim_type=os.getenv("SIM_TYPE", "simple"),
        episodes=int(os.getenv("EPISODES", 300)),
        tasks=300,
        avg_latency=avg_latency or 0.0
    )
    manifest_path = save_manifest_local(manifest)
    print(f"✅ Manifest saved → {manifest_path}")

    # ----------------------------------------------------------------------
    # 2️⃣ Upload artifacts to S3
    # ----------------------------------------------------------------------
    print(f"\n📦 Uploading artifacts to S3 under prefix: {prefix}")
    for fname in [
        "rl_weights.npy",
        "workload_results.csv",
        "workload_comparison.png",
        "reward_curve.png",
        "manifest.json"
    ]:
        path = os.path.join(DATA_DIR, fname)
        if os.path.exists(path):
            try:
                upload_file(path, key_prefix=prefix)
                print(f"✅ Uploaded → {fname}")
            except Exception as e:
                print(f"⚠️ Failed to upload {fname}: {e}")
        else:
            print(f"⚠️ Skipping missing file: {fname}")

    print("\n✅ Remote execution complete.")


if __name__ == "__main__":
    main()
