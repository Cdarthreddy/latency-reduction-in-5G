# train_rl.py  (Week 9 – Synthetic Workload Modeling)
from __future__ import annotations
import os, csv, random
from datetime import datetime
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from orchestrator.rl_orchestrator import RLBasedOrchestrator
from orchestrator.environment import Task
from orchestrator.sim_interface import get_simulator


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
DATA_DIR   = "data"
WORKLOADS  = os.path.join(DATA_DIR, "workloads.csv")
OUT_WEIGHTS = os.path.join(DATA_DIR, "rl_weights.npy")
OUT_CSV     = os.path.join(DATA_DIR, "workload_results.csv")
OUT_PNG     = os.path.join(DATA_DIR, "workload_comparison.png")
OUT_REWARD  = os.path.join(DATA_DIR, "reward_curve.png")

# ---------------------------------------------------------------------
def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------------------------
# Week 9: enhanced workload loader (backward compatible)
# ---------------------------------------------------------------------
def load_or_generate_workloads(n: int = 300) -> list[Task]:
    """
    Loads timestamped workloads (Week 9 schema) or falls back to legacy schema.
    Compatible columns:
        task_id, timestamp, app_type, size_mb, priority
        task_id, app_type, size_mb, priority
        task_id, size_mb, priority
    """
    ensure_dirs()
    tasks: list[Task] = []

    if os.path.exists(WORKLOADS):
        with open(WORKLOADS, "r") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            for row in reader:
                if not row: 
                    continue
                try:
                    # detect schema by column count
                    if len(row) == 5:
                        task_id, ts, app, size, prio = row
                    elif len(row) == 4:
                        task_id, app, size, prio = row
                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    else:  # old 3-col format
                        task_id, size, prio = row
                        ts, app = datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "IoT"

                    tasks.append(Task(int(task_id), app, float(size), prio))
                except Exception:
                    continue
        print(f"✅ Loaded {len(tasks)} tasks from {WORKLOADS}")
        return tasks

    # fallback: generate quick synthetic workload (rarely needed)
    print("⚠️  workloads.csv not found – generating dummy data.")
    with open(WORKLOADS, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task_id","timestamp","app_type","size_mb","priority"])
        for i in range(n):
            app = random.choice(["IoT","ARVR","VANET"])
            size = random.uniform(0.5,12.0)
            prio = random.choice(["low","medium","high"])
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            w.writerow([i, ts, app, f"{size:.3f}", prio])
            tasks.append(Task(i, app, size, prio))
    return tasks


# ---------------------------------------------------------------------
def plot_reward_curve(rewards: list[float]):
    plt.figure()
    plt.plot(range(1, len(rewards)+1), rewards)
    plt.title("Episode reward (sum of −latency_ms) – higher is better")
    plt.xlabel("Episode"); plt.ylabel("Total reward")
    plt.tight_layout()
    plt.savefig(OUT_REWARD, dpi=130); plt.close()


def plot_latency_box(edge_lats, cloud_lats, path, title):
    plt.figure()
    plt.boxplot([edge_lats, cloud_lats], labels=["edge","cloud"], showmeans=True)
    plt.title(title); plt.ylabel("Latency (ms)")
    plt.tight_layout(); plt.savefig(path, dpi=130); plt.close()


# ---------------------------------------------------------------------
def train_and_eval():
    ensure_dirs()
    SIM_CHOICE = os.getenv("SIM_TYPE","simple")
    sim = get_simulator(SIM_CHOICE)
    print(f"✅ Using simulator: {SIM_CHOICE}")

    # --- train --------------------------------------------------------
    orch = RLBasedOrchestrator(sim=sim, episodes=300)
    avg_lat_ms, rewards = orch.simulate_environment(num_tasks=300)
    np.save(OUT_WEIGHTS, np.array([avg_lat_ms]))
    plot_reward_curve(rewards)

    # --- eval ---------------------------------------------------------
    tasks = load_or_generate_workloads()
    eval_orch = RLBasedOrchestrator(sim=sim, episodes=1, epsilon=0.0)
    results = []
    for t in tasks:
        state = (t.app_type.lower(), t.priority.lower())
        action = eval_orch.choose_action_greedy(state)
        node, lat = eval_orch.assign_and_execute(t, action)
        results.append((t.task_id, node, lat))

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task_id","node","latency_ms"])
        w.writerows(results)

    edge = [lat for _,n,lat in results if "edge" in n.lower()]
    cloud = [lat for _,n,lat in results if "cloud" in n.lower()]
    plot_latency_box(edge, cloud, OUT_PNG, "Workload Latency Comparison (Week-9 RL)")

    print("\n✅ Outputs:")
    print(f"  {OUT_WEIGHTS}\n  {OUT_REWARD}\n  {OUT_CSV}\n  {OUT_PNG}")


# ---------------------------------------------------------------------
if __name__ == "__main__":
    train_and_eval()
