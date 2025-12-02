"""
Analysis script to aggregate results from multiple S3 runs or local files.
Downloads all workload_results.csv files and generates summary statistics.

Usage:
    # Analyze S3 results (requires AWS credentials)
    python -m analysis.analyze_results
    
    # Analyze local file (no AWS needed)
    USE_LOCAL=1 python -m analysis.analyze_results
    # Or on Windows:
    set USE_LOCAL=1 && python -m analysis.analyze_results
    
    # Alternative: Run directly
    python analysis/analyze_results.py
"""
import os
import io
import sys

try:
    import pandas as pd
except ImportError as e:
    print("[ERROR] Missing required dependency: pandas")
    print(f"Error: {e}")
    print("\n[INFO] Please install pandas:")
    print("  pip install pandas")
    print("\nOr install all dependencies:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

# Handle imports - works both as module and as standalone script
_script_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_script_dir)

# Add both script directory and parent directory to path
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Try different import strategies for report_utils
try:
    # Strategy 1: Package import (works when run as: python -m analysis.analyze_results)
    from analysis.report_utils import aggregate_latency, plot_latency_distribution, write_summary_md
except ImportError:
    try:
        # Strategy 2: Direct import from same directory (works when run as: python analysis/analyze_results.py)
        from report_utils import aggregate_latency, plot_latency_distribution, write_summary_md
    except ImportError as e:
        error_msg = str(e)
        if "No module named" in error_msg or "cannot import name" in error_msg:
            missing_module = error_msg.split("'")[1] if "'" in error_msg else "unknown"
            print(f"[ERROR] Failed to import report_utils or its dependencies.")
            print(f"Error: {e}")
            
            # Check if report_utils.py exists
            report_utils_path = os.path.join(_script_dir, 'report_utils.py')
            if not os.path.exists(report_utils_path):
                print(f"[ERROR] report_utils.py not found at: {report_utils_path}")
            else:
                print(f"[INFO] report_utils.py found, but missing dependency: {missing_module}")
                print("\n[INFO] report_utils requires: pandas, numpy, matplotlib")
                print("Please install missing dependencies:")
                print("  pip install pandas numpy matplotlib")
                print("\nOr install all dependencies:")
                print("  pip install -r requirements.txt")
        else:
            print(f"[ERROR] Failed to import report_utils: {e}")
            print(f"[INFO] Script directory: {_script_dir}")
            print(f"[INFO] Parent directory: {_parent_dir}")
        sys.exit(1)

S3_BUCKET = os.getenv("S3_BUCKET", "latency-results-project")
REGION = os.getenv("AWS_REGION", "us-east-1")
DATA_DIR = os.getenv("DATA_DIR", "data")


def load_local_results(data_dir: str = DATA_DIR) -> pd.DataFrame:
    """
    Load workload_results.csv from local data directory.
    
    Args:
        data_dir: Directory containing workload_results.csv
        
    Returns:
        pd.DataFrame: DataFrame with results, or empty DataFrame if file not found.
    """
    local_file = os.path.join(data_dir, "workload_results.csv")
    
    if not os.path.exists(local_file):
        print(f"[INFO] Local file not found: {local_file}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(local_file)
        df["run_id"] = "local-run"  # Mark as local run
        print(f"[OK] Loaded local file: {local_file} ({len(df)} rows)")
        return df
    except Exception as e:
        print(f"[ERROR] Failed to load local file {local_file}: {e}")
        return pd.DataFrame()


def download_all_runs(prefix="runs/"):
    """
    Download all workload_results.csv files from S3 and combine into a single DataFrame.
    
    Returns:
        pd.DataFrame: Combined DataFrame with all runs, or empty DataFrame if no files found.
    """
    # Import boto3 only when needed (for S3 operations)
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
    except ImportError as e:
        print("[ERROR] Missing required AWS dependencies (boto3, botocore).")
        print(f"Error: {e}")
        print("\n[INFO] To use S3, please install:")
        print("  pip install boto3 botocore")
        print("\nOr use local files instead (no AWS needed):")
        print("  USE_LOCAL=1 python -m analysis.analyze_results")
        return pd.DataFrame()
    
    try:
        s3 = boto3.client("s3", region_name=REGION)
    except (NoCredentialsError, Exception) as e:
        print(f"[ERROR] Failed to initialize S3 client: {e}")
        print("[INFO] Make sure AWS credentials are configured or run this script on an EC2 instance with IAM role.")
        return pd.DataFrame()
    
    paginator = s3.get_paginator("list_objects_v2")
    data_frames = []
    downloaded_count = 0
    
    try:
        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
            if "Contents" not in page:
                continue
                
            for obj in page["Contents"]:
                if obj["Key"].endswith("workload_results.csv"):
                    try:
                        buf = io.BytesIO()
                        s3.download_fileobj(S3_BUCKET, obj["Key"], buf)
                        buf.seek(0)
                        df = pd.read_csv(buf)
                        
                        # Extract run_id from S3 key (format: runs/run-YYYYMMDDTHHMMSSZ/workload_results.csv)
                        key_parts = obj["Key"].split("/")
                        if len(key_parts) >= 2:
                            df["run_id"] = key_parts[1]
                        else:
                            df["run_id"] = "unknown"
                        
                        data_frames.append(df)
                        downloaded_count += 1
                        print(f"[OK] Downloaded: {obj['Key']} ({len(df)} rows)")
                    except Exception as e:
                        print(f"[WARN] Failed to process {obj['Key']}: {e}")
                        continue
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'NoSuchBucket':
            print(f"[ERROR] S3 bucket '{S3_BUCKET}' does not exist.")
        elif error_code in ('AccessDenied', 'InvalidAccessKeyId', 'UnauthorizedOperation'):
            print(f"[ERROR] Access denied to S3 bucket '{S3_BUCKET}'. Check your AWS credentials.")
            print(f"\n[INFO] Possible issues:")
            print(f"  1. AWS credentials not configured (run 'aws configure')")
            print(f"  2. IAM user/role doesn't have S3 read permissions")
            print(f"  3. Wrong AWS credentials profile")
            print(f"\n[INFO] To analyze local files instead (no AWS needed):")
            print(f"  USE_LOCAL=1 python -m analysis.analyze_results")
        else:
            print(f"[ERROR] S3 error: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"[ERROR] Unexpected error downloading from S3: {e}")
        return pd.DataFrame()
    
    if not data_frames:
        print(f"[WARN] No workload_results.csv files found in s3://{S3_BUCKET}/{prefix}")
        return pd.DataFrame()
    
    print(f"[OK] Downloaded {downloaded_count} result file(s)")
    combined_df = pd.concat(data_frames, ignore_index=True)
    print(f"[OK] Combined DataFrame: {len(combined_df)} total rows")
    return combined_df


def main():
    """Main entry point for result aggregation."""
    use_local = os.getenv("USE_LOCAL", "").lower() in ("true", "1", "yes")
    
    if use_local:
        print(f"[START] Loading results from local directory: {DATA_DIR}")
        df = load_local_results()
    else:
        print(f"[START] Fetching runs from S3 bucket: {S3_BUCKET} (region: {REGION})")
        df = download_all_runs()
        
        # If S3 fails and no data, try local as fallback
        if df.empty:
            print("\n[INFO] S3 download failed. Trying local file as fallback...")
            df = load_local_results()
    
    if df.empty:
        print("\n[ERROR] No data to analyze.")
        print("\n[INFO] Options to get data:")
        print("  1. Configure AWS credentials for S3 access")
        print("  2. Use local file: Set USE_LOCAL=1 environment variable")
        print("  3. Ensure data/workload_results.csv exists locally")
        print("\nTo use local file instead of S3:")
        print("  # Windows:")
        print("  set USE_LOCAL=1")
        print("  python -m analysis.analyze_results")
        print("  # Linux/Mac:")
        print("  USE_LOCAL=1 python -m analysis.analyze_results")
        return 1
    
    print(f"[OK] Processing {len(df)} rows from {df['run_id'].nunique()} run(s)")
    
    # Aggregate statistics
    try:
        stats_df = aggregate_latency(df)
    except Exception as e:
        print(f"[ERROR] Failed to aggregate latency: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    if stats_df.empty:
        print("[WARN] No statistics generated. Check data format.")
        return 1
    
    # Create output directory
    os.makedirs("analysis/out", exist_ok=True)
    
    # Save statistics
    try:
        stats_df.to_csv("analysis/out/summary_stats.csv", index=False)
        print(f"[OK] Saved summary stats -> analysis/out/summary_stats.csv")
    except Exception as e:
        print(f"[ERROR] Failed to save summary stats: {e}")
        return 1
    
    # Generate visualizations
    try:
        plot_latency_distribution(df, "analysis/out/latency_summary.png")
        print(f"[OK] Saved plot -> analysis/out/latency_summary.png")
    except Exception as e:
        print(f"[WARN] Failed to generate plot: {e}")
        import traceback
        traceback.print_exc()
    
    # Generate markdown summary
    try:
        write_summary_md(stats_df, "analysis/out/summary.md")
        print(f"[OK] Saved summary -> analysis/out/summary.md")
    except Exception as e:
        print(f"[WARN] Failed to generate markdown summary: {e}")
    
    print("[OK] Aggregation complete -> analysis/out/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
