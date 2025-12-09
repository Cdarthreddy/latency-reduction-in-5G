import os
from orchestrator.workload_generator import WorkloadGenerator
from train_rl import train_and_eval
from utils.s3_io import upload_file
from utils.manifest import create_manifest, save_manifest_local
from config import DATA_DIR, get_s3_prefix, RUN_ID

# Import safe print utility
try:
    from utils.console import safe_print
except ImportError:
    def safe_print(msg: str, fallback: str | None = None) -> None:
        try:
            print(msg)
        except UnicodeEncodeError:
            if fallback:
                print(fallback)
            else:
                print(msg.encode('ascii', 'replace').decode('ascii'))

# Import CloudWatch utilities
try:
    from utils.cloudwatch import get_logger, get_metrics
    cw_logger = get_logger()
    cw_metrics = get_metrics()
except ImportError:
    # Fallback if CloudWatch module not available
    cw_logger = None
    cw_metrics = None

def ensure_workload():
    """Ensures workloads.csv exists before training."""
    workload_file = os.path.join(DATA_DIR, "workloads.csv")
    if not os.path.exists(workload_file):
        safe_print("[CONFIG] No workloads.csv found -> generating new one...",
                   fallback="[CONFIG] No workloads.csv found -> generating new one...")
        if cw_logger:
            cw_logger.info("Generating new workload file")
        WorkloadGenerator(num_tasks=300, poisson_lambda=3.0).generate()
    else:
        safe_print("[OK] Workload already present; re-using existing file.",
                   fallback="[OK] Workload already present; re-using existing file.")
        if cw_logger:
            cw_logger.info("Using existing workload file")


def main():
    """Main entrypoint for remote orchestration."""
    if cw_logger:
        cw_logger.info(f"Starting remote orchestration run: {RUN_ID}")
        cw_logger.info(f"Config: region={os.getenv('AWS_REGION', 'us-east-1')}, "
                      f"bucket={os.getenv('S3_BUCKET', 'latency-results-project')}")
    
    ensure_workload()

    # Train + evaluate RL orchestrator
    safe_print("[START] Starting training + evaluation...",
               fallback="[START] Starting training + evaluation...")
    if cw_logger:
        cw_logger.info("Starting RL training and evaluation phase")
    
    try:
        # Configuration from Environment
        episodes = int(os.getenv("EPISODES", 1000))  # Default to 1000 to match train_rl default
        sim_type = os.getenv("SIM_TYPE", "simple")  # Default to simple

        avg_latency = train_and_eval(episodes=episodes, sim_type=sim_type)  # returns average latency
        if cw_metrics and avg_latency:
            cw_metrics.put_metric("TrainingAverageLatency", avg_latency, "Milliseconds",
                                dimensions={"RunID": RUN_ID})
    except Exception as e:
        safe_print(f"[ERROR] Training failed: {e}", fallback=f"[ERROR] Training failed: {e}")
        if cw_logger:
            cw_logger.error(f"Training failed: {str(e)}")
        if cw_metrics:
            cw_metrics.put_completion_metric(False, 300)
        raise
    
    prefix = get_s3_prefix()

    # ----------------------------------------------------------------------
    # 1. Create and save manifest
    # ----------------------------------------------------------------------
    manifest = create_manifest(
        sim_type=os.getenv("SIM_TYPE", "simple"),
        episodes=int(os.getenv("EPISODES", 300)),
        tasks=300,
        avg_latency=avg_latency or 0.0
    )
    manifest_path = save_manifest_local(manifest)
    safe_print(f"[OK] Manifest saved -> {manifest_path}",
               fallback=f"[OK] Manifest saved -> {manifest_path}")
    if cw_logger:
        cw_logger.info(f"Manifest created: {manifest_path}")

    # ----------------------------------------------------------------------
    # 2. Upload artifacts to S3
    # ----------------------------------------------------------------------
    safe_print(f"\n[UPLOAD] Uploading artifacts to S3 under prefix: {prefix}",
               fallback=f"\n[UPLOAD] Uploading artifacts to S3 under prefix: {prefix}")
    if cw_logger:
        cw_logger.info(f"Starting S3 upload to prefix: {prefix}")
    
    uploaded_count = 0
    failed_count = 0
    
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
                safe_print(f"[OK] Uploaded -> {fname}", fallback=f"[OK] Uploaded -> {fname}")
                if cw_logger:
                    cw_logger.info(f"Successfully uploaded {fname}")
                uploaded_count += 1
            except Exception as e:
                safe_print(f"[WARN] Failed to upload {fname}: {e}",
                          fallback=f"[WARN] Failed to upload {fname}: {e}")
                if cw_logger:
                    cw_logger.warning(f"Failed to upload {fname}: {str(e)}")
                failed_count += 1
        else:
            safe_print(f"[WARN] Skipping missing file: {fname}",
                      fallback=f"[WARN] Skipping missing file: {fname}")
            if cw_logger:
                cw_logger.warning(f"Missing file: {fname}")
            failed_count += 1

    # Publish completion metrics
    if cw_metrics:
        cw_metrics.put_metric("S3UploadSuccess", uploaded_count, "Count",
                            dimensions={"RunID": RUN_ID})
        cw_metrics.put_metric("S3UploadFailure", failed_count, "Count",
                            dimensions={"RunID": RUN_ID})
        cw_metrics.put_completion_metric(True, 300)

    safe_print("\n[OK] Remote execution complete.",
               fallback="\n[OK] Remote execution complete.")
    if cw_logger:
        cw_logger.info(f"Remote orchestration run completed: {RUN_ID} | "
                      f"Uploaded: {uploaded_count}, Failed: {failed_count}")


if __name__ == "__main__":
    main()
