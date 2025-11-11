# train_rl.py  (WEEK 8)
from __future__ import annotations
import os
import csv
import random
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless safe
import matplotlib.pyplot as plt
import seaborn as sns

from orchestrator.environment import Node, Task
from orchestrator.random_orchestrator import RandomOrchestrator
from orchestrator.rule_orchestrator import RuleBasedOrchestrator
from orchestrator.rl_orchestrator import RLBasedOrchestrator
from orchestrator.sim_interface import get_simulator

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
DATA_DIR = "data"
WORKLOADS = os.path.join(DATA_DIR, "workloads.csv")
OUT_CSV   = os.path.join(DATA_DIR, "workload_results.csv")
OUT_PNG   = os.path.join(DATA_DIR, "workload_comparison.png")

# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------
def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_or_generate_workloads(n: int = 300) -> list[Task]:
    ensure_dirs()
    tasks: list[Task] = []

    if os.path.exists(WORKLOADS):
        df = pd.read_csv(WORKLOADS)
        for _, row in df.iterrows():
            tasks.append(Task(int(row.task_id), row.app_type, float(row.size_mb), row.priority))
        return tasks

    # Generate fresh workloads
    with open(WORKLOADS, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task_id", "app_type", "size_mb", "priority"])
        for i in range(n):
            app_type = random.choice(["IoT", "ARVR", "VANET"])
            size = random.uniform(0.5, 12.0)
            prio = random.choice(["high", "medium", "low"])
            w.writerow([i, app_type, f"{size:.3f}", prio])
            tasks.append(Task(i, app_type, size, prio))
    return tasks

# ---------------------------------------------------------------------
# Week 8 – Simulator Validation Run
# ---------------------------------------------------------------------
def train_and_eval():
    ensure_dirs()
    SIM_CHOICE = os.getenv("SIM_TYPE", "simple")
    sim = get_simulator(SIM_CHOICE)
    print(f"✅ Using simulator: {SIM_CHOICE}")

    # Create edge and cloud nodes
    edge = Node(0, "edge", 2.0)
    cloud = Node(1, "cloud", 8.0)

    tasks = load_or_generate_workloads(300)

    strategies = {
        "Random": RandomOrchestrator(edge, cloud),
        "Rule":   RuleBasedOrchestrator(edge, cloud),
        "RL":     RLBasedOrchestrator(edge, cloud, episodes=50)  # stub for compatibility
    }

    all_records = []
    for name, orch in strategies.items():
        latencies = []
        for t in tasks:
            if name == "Rule":
                node = orch.edge if (t.size_mb < 5 or t.priority == "high") else orch.cloud
                latency = node.execute_task(t, network_sim=sim)
                node_name = node.name
            elif name == "Random":
                node = orch.edge if random.choice([True, False]) else orch.cloud
                latency = node.execute_task(t, network_sim=sim)
                node_name = node.name
            else:
                # RL stub just randomly assigns too, no training yet
                node = orch.edge if random.choice([True, False]) else orch.cloud
                latency = node.execute_task(t, network_sim=sim)
                node_name = node.name

            all_records.append({
                "strategy": name,
                "app_type": t.app_type,
                "size_mb": t.size_mb,
                "priority": t.priority,
                "node": node_name,
                "latency": latency
            })
            latencies.append(latency)
        print(f"✅ {name} done | avg latency: {sum(latencies)/len(latencies):.2f} ms")

    df = pd.DataFrame(all_records)
    df.to_csv(OUT_CSV, index=False)

    # Visualization
    plt.figure(figsize=(9,6))
    sns.boxplot(x="app_type", y="latency", hue="strategy", data=df, palette="Set2")
    plt.title("Week-8 Latency Comparison (Simulator Validation)")
    plt.xlabel("Application Type")
    plt.ylabel("Latency (ms)")
    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=130)
    plt.close()

    print(f"\n✅ Outputs generated:\n  {OUT_CSV}\n  {OUT_PNG}")

# ---------------------------------------------------------------------
if __name__ == "__main__":
    train_and_eval()
