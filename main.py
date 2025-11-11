# main.py
from orchestrator.environment import Task, Node
from orchestrator.random_orchestrator import RandomOrchestrator
from orchestrator.rule_orchestrator import RuleBasedOrchestrator
from orchestrator.rl_orchestrator import RLBasedOrchestrator
from orchestrator.sim_interface import get_simulator
from orchestrator.workload_generator import WorkloadGenerator
import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ---------------------------------------------------------------------
# Main execution pipeline
# ---------------------------------------------------------------------
def run_with_workload():
    # Step 1️⃣ – Generate or load workloads
    gen = WorkloadGenerator(num_tasks=300)
    gen.generate()
    df_work = pd.read_csv("data/workloads.csv")

    # Step 2️⃣ – Initialize network simulator
    SIM_CHOICE = os.getenv("SIM_TYPE", "simple")  # default = SimpleSimulator
    sim = get_simulator(SIM_CHOICE)
    print(f"✅ Using simulator: {SIM_CHOICE}")

    all_records = []

    # Step 3️⃣ – Node factory
    def make_nodes():
        return Node(0, "edge", 2.0), Node(1, "cloud", 8.0)

    # Step 4️⃣ – Strategy registry
    strategies = {
        "Random": RandomOrchestrator,
        "Rule": RuleBasedOrchestrator,
        "RL": RLBasedOrchestrator,
    }

    # Step 5️⃣ – Evaluate each strategy
    for name, OrchClass in strategies.items():
        edge, cloud = make_nodes()

        if name == "RL":
            orch = OrchClass(edge, cloud, episodes=300)
            orch.set_simulator(sim)       # ✅ attach simulator dynamically
        else:
            orch = OrchClass(edge, cloud)

        latencies = []
        for _, row in df_work.iterrows():
            task = Task(int(row.task_id), row.app_type, float(row.size_mb), row.priority)

            if name == "RL":
                # Use simple ε-greedy policy for inference
                state = (task.app_type.lower(), task.priority.lower())
                action = random.choice([0, 1]) if random.random() < 0.3 else 0  # explore a bit
                node_name, latency = orch.assign_and_execute(task, action)

            elif name == "Rule":
                node = orch.edge if (task.size_mb < 5 or task.priority == "high") else orch.cloud
                latency = node.execute_task(task, network_sim=sim)
                node_name = node.name

            else:  # Random baseline
                node = orch.edge if random.choice([True, False]) else orch.cloud
                latency = node.execute_task(task, network_sim=sim)
                node_name = node.name

            all_records.append({
                "strategy": name,
                "app_type": row.app_type,
                "size_mb": row.size_mb,
                "priority": row.priority,
                "node": node_name,
                "latency": latency
            })
            latencies.append(latency)

        print(f"✅ {name} done | avg latency: {np.mean(latencies):.2f} ms")

    # Step 6️⃣ – Save & visualize
    df = pd.DataFrame(all_records)
    df.to_csv("data/workload_results.csv", index=False)
    plot_latency_by_app(df)

    print("\n✅ Outputs generated:")
    print("  data/workload_results.csv")
    print("  data/workload_comparison.png")


# ---------------------------------------------------------------------
# Plot results
# ---------------------------------------------------------------------
def plot_latency_by_app(df: pd.DataFrame):
    plt.close("all")
    plt.figure(figsize=(9, 6))
    sns.boxplot(
        x="app_type",
        y="latency",
        hue="strategy",
        data=df,
        palette="Set2"
    )
    plt.title("Latency Comparison per App Type & Strategy")
    plt.ylabel("Latency (ms)")
    plt.xlabel("Application Type")
    plt.legend(title="Strategy")
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig("data/workload_comparison.png", dpi=130)
    plt.close()


# ---------------------------------------------------------------------
if __name__ == "__main__":
    run_with_workload()
