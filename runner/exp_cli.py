# runner/exp_cli.py
"""
Example usage:
    python runner/exp_cli.py --episodes 100 200 300 --tasks 150 --sim simple
"""

import argparse, os, subprocess
from datetime import datetime, timezone

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--episodes", nargs="+", type=int, default=[200, 300])
    p.add_argument("--tasks", type=int, default=300)
    p.add_argument("--sim", type=str, default="simple")
    args = p.parse_args()

    for ep in args.episodes:
        run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        env = os.environ.copy()
        env["RUN_ID"] = run_id
        env["SIM_TYPE"] = args.sim
        print(f"\n[START] Starting trial {run_id} | episodes={ep}, tasks={args.tasks}, sim={args.sim}")
        subprocess.run(
            ["python", "main_remote.py"],
            env=env,
            check=False
        )
        print(f"[OK] Trial complete -> {run_id}\n{'-'*60}")

if __name__ == "__main__":
    main()
