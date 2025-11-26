# train_rl.py  – Week 10 (AWS-ready)
from __future__ import annotations
import os, csv, random
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from orchestrator.rl_orchestrator import RLBasedOrchestrator
from orchestrator.environment import Task
from orchestrator.sim_interface import get_simulator
from datetime import datetime
from config import DATA_DIR


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
WORKLOADS   = os.path.join(DATA_DIR, "workloads.csv")
OUT_WEIGHTS = os.path.join(DATA_DIR, "rl_weights.npy")
OUT_CSV     = os.path.join(DATA_DIR, "workload_results.csv")
OUT_PNG     = os.path.join(DATA_DIR, "workload_comparison.png")
OUT_REWARD  = os.path.join(DATA_DIR, "reward_curve.png")

# ---------------------------------------------------------------------
def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------------------------
# Load workloads (timestamped / legacy compatible)
# ---------------------------------------------------------------------
def load_or_generate_workloads(n: int = 300) -> list[Task]:
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
                    if len(row) == 5:
                        task_id, ts, app, size, prio = row
                    elif len(row) == 4:
                        task_id, app, size, prio = row
                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        task_id, size, prio = row
                        app = "IoT"
                        ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    tasks.append(Task(int(task_id), app, float(size), prio))
                except Exception:
                    continue
        print(f"✅ Loaded {len(tasks)} tasks from {WORKLOADS}")
        return tasks

    # fallback dummy set
    print("⚠️ workloads.csv missing – generating dummy data.")
    with open(WORKLOADS, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task_id","timestamp","app_type","size_mb","priority"])
        for i in range(n):
            app  = random.choice(["IoT","ARVR","VANET"])
            size = random.uniform(0.5,12.0)
            prio = random.choice(["low","medium","high"])
            ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            w.writerow([i, ts, app, f"{size:.3f}", prio])
            tasks.append(Task(i, app, size, prio))
    return tasks


# ---------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------
def plot_reward_curve(rewards: list[float]):
    plt.figure()
    plt.plot(range(1, len(rewards)+1), rewards)
    plt.title("Episode Reward (sum of −latency_ms) – higher is better")
    plt.xlabel("Episode"); plt.ylabel("Total Reward")
    plt.tight_layout(); plt.savefig(OUT_REWARD, dpi=130); plt.close()

def plot_latency_box(edge_lats, cloud_lats, path, title):
    plt.figure()
    plt.boxplot([edge_lats, cloud_lats], labels=["edge","cloud"], showmeans=True)
    plt.title(title); plt.ylabel("Latency (ms)")
    plt.tight_layout(); plt.savefig(path, dpi=130); plt.close()


# ---------------------------------------------------------------------
# TRAIN + EVAL (exported for main_remote.py)
# ---------------------------------------------------------------------
def train_and_eval(sim_choice: str = "simple", episodes: int = 300) -> dict:
    """
    Runs RL training + evaluation, returns artifact paths for upload.
    """
    ensure_dirs()
    sim = get_simulator(sim_choice)
    print(f"✅ Using simulator: {sim_choice}")

    # --- Train phase -------------------------------------------------
    orch = RLBasedOrchestrator(sim=sim, episodes=episodes)
    avg_lat_ms, rewards = orch.simulate_environment(num_tasks=300)
    np.save(OUT_WEIGHTS, np.array([avg_lat_ms]))
    plot_reward_curve(rewards)

    # --- Evaluation phase --------------------------------------------
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

    edge = [lat for _,n,lat in results if "edge"  in n.lower()]
    cloud= [lat for _,n,lat in results if "cloud" in n.lower()]
    plot_latency_box(edge, cloud, OUT_PNG, "Workload Latency Comparison (AWS-Ready RL)")

    print("\n✅ Training + Evaluation complete.")
    print(f"  {OUT_WEIGHTS}\n  {OUT_REWARD}\n  {OUT_CSV}\n  {OUT_PNG}")

    return {
        "weights": OUT_WEIGHTS,
        "reward_plot": OUT_REWARD,
        "results_csv": OUT_CSV,
        "latency_plot": OUT_PNG
    }


# ---------------------------------------------------------------------
if __name__ == "__main__":
    train_and_eval()
