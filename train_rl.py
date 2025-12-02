# train_rl.py  – Week 10 (AWS-ready) + Week 11 (CloudWatch)
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

# Import CloudWatch utilities (optional - will work without AWS credentials)
try:
    from utils.cloudwatch import get_logger, get_metrics
    cw_logger = get_logger()
    cw_metrics = get_metrics()
except ImportError:
    cw_logger = None
    cw_metrics = None


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
        print(f"[OK] Loaded {len(tasks)} tasks from {WORKLOADS}")
        return tasks

    # fallback dummy set
    print("[WARN] workloads.csv missing - generating dummy data.")
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
    # Use tick_labels instead of labels (matplotlib 3.9+)
    bp = plt.boxplot([edge_lats, cloud_lats], showmeans=True)
    plt.xticks([1, 2], ["edge", "cloud"])
    plt.title(title); plt.ylabel("Latency (ms)")
    plt.tight_layout(); plt.savefig(path, dpi=130); plt.close()


# ---------------------------------------------------------------------
# TRAIN + EVAL (exported for main_remote.py)
# ---------------------------------------------------------------------
def train_and_eval(sim_choice: str = "simple", episodes: int = 300) -> dict:
    """
    Runs RL training + evaluation, returns artifact paths for upload.
    Now includes CloudWatch logging and metrics.
    """
    ensure_dirs()
    sim = get_simulator(sim_choice)
    print(f"[OK] Using simulator: {sim_choice}")
    
    if cw_logger:
        cw_logger.info(f"Starting RL training: simulator={sim_choice}, episodes={episodes}")

    # --- Train phase -------------------------------------------------
    if cw_logger:
        cw_logger.info("Beginning training phase")
    
    orch = RLBasedOrchestrator(sim=sim, episodes=episodes)
    avg_lat_ms, rewards = orch.simulate_environment(num_tasks=300)
    
    # Log training metrics periodically
    if cw_metrics and rewards:
        # Log every 50th episode to avoid too many API calls
        for i in range(0, len(rewards), max(1, len(rewards) // 10)):
            ep_num = i + 1
            cw_metrics.put_training_metric(ep_num, rewards[i], -rewards[i] / 300)
        
        # Log final training metrics
        final_reward = rewards[-1] if rewards else 0.0
        cw_metrics.put_training_metric(episodes, final_reward, avg_lat_ms)
        cw_metrics.put_metric("TrainingAverageLatency", avg_lat_ms, "Milliseconds")
    
    if cw_logger:
        cw_logger.info(f"Training complete: avg_latency={avg_lat_ms:.2f}ms, "
                      f"final_reward={rewards[-1] if rewards else 0.0:.2f}")
    
    np.save(OUT_WEIGHTS, np.array([avg_lat_ms]))
    plot_reward_curve(rewards)

    # --- Evaluation phase --------------------------------------------
    if cw_logger:
        cw_logger.info("Beginning evaluation phase")
    
    tasks = load_or_generate_workloads()
    eval_orch = RLBasedOrchestrator(sim=sim, episodes=1, epsilon=0.0)
    results = []
    # Reset node loads for evaluation
    eval_orch.edge.reset_load()
    eval_orch.cloud.reset_load()
    
    edge_latencies = []
    cloud_latencies = []
    
    for t in tasks:
        # Use enhanced state representation with node loads
        state = eval_orch._get_state(t, eval_orch.edge.current_load, eval_orch.cloud.current_load)
        action = eval_orch.choose_action_greedy(state)
        node, lat = eval_orch.assign_and_execute(t, action)
        results.append((t.task_id, node, lat))
        
        # Log latency metrics (sample every 10th task to avoid too many API calls)
        if cw_metrics and t.task_id % 10 == 0:
            node_type = "edge" if "edge" in node.lower() else "cloud"
            cw_metrics.put_latency_metric(lat, node_type, t.app_type)
        
        if "edge" in node.lower():
            edge_latencies.append(lat)
        else:
            cloud_latencies.append(lat)

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task_id","node","latency_ms"])
        w.writerows(results)

    edge = [lat for _,n,lat in results if "edge"  in n.lower()]
    cloud= [lat for _,n,lat in results if "cloud" in n.lower()]
    plot_latency_box(edge, cloud, OUT_PNG, "Workload Latency Comparison (AWS-Ready RL)")
    
    # Log evaluation summary metrics
    if cw_metrics:
        if edge_latencies:
            cw_metrics.put_metric("EvaluationEdgeAvgLatency", np.mean(edge_latencies), "Milliseconds")
        if cloud_latencies:
            cw_metrics.put_metric("EvaluationCloudAvgLatency", np.mean(cloud_latencies), "Milliseconds")
        cw_metrics.put_metric("EvaluationEdgeTaskCount", len(edge_latencies), "Count")
        cw_metrics.put_metric("EvaluationCloudTaskCount", len(cloud_latencies), "Count")

    print("\n[OK] Training + Evaluation complete.")
    print(f"  {OUT_WEIGHTS}\n  {OUT_REWARD}\n  {OUT_CSV}\n  {OUT_PNG}")
    
    if cw_logger:
        cw_logger.info(f"Evaluation complete: {len(results)} tasks processed, "
                      f"edge={len(edge_latencies)}, cloud={len(cloud_latencies)}")
    
    # Return average latency for main_remote.py
    avg_latency = avg_lat_ms if isinstance(avg_lat_ms, (int, float)) else float(avg_lat_ms)

    return avg_latency


# ---------------------------------------------------------------------
if __name__ == "__main__":
    train_and_eval()
