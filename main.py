# main.py
from orchestrator.environment import Task, Node
from orchestrator.random_orchestrator import RandomOrchestrator
from orchestrator.rule_orchestrator import RuleBasedOrchestrator
from orchestrator.rule_orchestrator import RuleBasedOrchestrator
from orchestrator.rl_orchestrator import RLBasedOrchestrator
from orchestrator.environment import Node, Task # Ensure Node/Task are imported for static classes
from orchestrator.sim_interface import get_simulator
from orchestrator.workload_generator import WorkloadGenerator
import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
import seaborn as sns
import os

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

# ---------------------------------------------------------------------
# Static Baselines
# ---------------------------------------------------------------------
class StaticEdgeOrchestrator:
    """Always assigns to Edge."""
    def __init__(self, edge: Node, cloud: Node):
        self.edge = edge
    def assign_task(self, task: Task):
        return self.edge.name, self.edge.execute_task(task)[0] # Return name, latency (ignore energy for signature compat in simple loop, but we need energy)
    
    def execute_task(self, task, network_sim=None):
        return self.edge.execute_task(task, network_sim)

class StaticCloudOrchestrator:
    """Always assigns to Cloud."""
    def __init__(self, edge: Node, cloud: Node):
        self.cloud = cloud
    def execute_task(self, task, network_sim=None):
        return self.cloud.execute_task(task, network_sim)

# ---------------------------------------------------------------------
# Main execution pipeline
# ---------------------------------------------------------------------
def run_with_workload():
    # Step 1 - Generate or load workloads
    # Use Poisson lambda=3.0 as per proposal
    gen = WorkloadGenerator(num_tasks=300, poisson_lambda=3.0)
    gen.generate()
    df_work = pd.read_csv("data/workloads.csv")

    # Step 2 - Initialize network simulator
    SIM_CHOICE = os.getenv("SIM_TYPE", "simple")  # default = FiveGDistributedSimulator
    sim = get_simulator(SIM_CHOICE)
    safe_print(f"[OK] Using simulator: {SIM_CHOICE}", fallback=f"[OK] Using simulator: {SIM_CHOICE}")

    all_records = []

    # Step 3 - Node factory
    def make_nodes():
        return Node(0, "edge", 2.0), Node(1, "cloud", 8.0)

    # Step 4 - Strategy registry
    strategies = {
        "Random": RandomOrchestrator,
        "Rule": RuleBasedOrchestrator,
        "RL": RLBasedOrchestrator,
        "StaticEdge": StaticEdgeOrchestrator,
        "StaticCloud": StaticCloudOrchestrator,
    }

    # Step 5 - Evaluate each strategy
    for name, OrchClass in strategies.items():
        edge, cloud = make_nodes()

        if name == "RL":
            orch = OrchClass(edge, cloud, episodes=300)
            orch.set_simulator(sim)       # attach simulator dynamically
            orch.set_simulator(sim)       # attach simulator dynamically
            
            # RETRAIN because we changed the environment physics (Bandwidth 100 -> 20)
            safe_print("[INFO] Retraining RL agent to adapt to new 20Mbps constraints...")
            orch.simulate_environment(num_tasks=300) # One training pass
            orch.save_weights("data/rl_weights.npy")
            
            # Load pre-trained weights if available (critical for valid comparison)
            orch.load_weights("data/rl_weights.npy")
        else:
            orch = OrchClass(edge, cloud)

        latencies = []
        energies = []
        for _, row in df_work.iterrows():
            task = Task(int(row.task_id), row.app_type, float(row.size_mb), row.priority)

            energy = 0.0
            if name == "RL":
                # Use enhanced state representation with node loads
                state = orch._get_state(task, orch.edge.current_load, orch.cloud.current_load)
                action = orch.choose_action_greedy(state)
                # Updated unpacked: node, latency, energy
                node_name, latency, energy = orch.assign_and_execute(task, action)

            elif name == "Rule":
                node = orch.edge if (task.size_mb < 5 or task.priority == "high") else orch.cloud
                # Updated unpacked: latency, energy
                latency, energy = node.execute_task(task, network_sim=sim)
                node_name = node.name

            elif name == "StaticEdge":
                node = orch.edge
                latency, energy = node.execute_task(task, network_sim=sim)
                node_name = node.name

            elif name == "StaticCloud":
                node = orch.cloud
                latency, energy = node.execute_task(task, network_sim=sim)
                node_name = node.name

            else:  # Random baseline
                node = orch.edge if random.choice([True, False]) else orch.cloud
                # Updated unpacked: latency, energy
                latency, energy = node.execute_task(task, network_sim=sim)
                node_name = node.name

            all_records.append({
                "strategy": name,
                "app_type": row.app_type,
                "size_mb": row.size_mb,
                "priority": row.priority,
                "node": node_name,
                "latency": latency,
                "energy": energy
            })
            latencies.append(latency)
            energies.append(energy)

        safe_print(f"[OK] {name} done | avg lat: {np.mean(latencies):.2f} ms | avg energy: {np.mean(energies):.2f} J",
                   fallback=f"[OK] {name} done | avg lat: {np.mean(latencies):.2f} ms | avg energy: {np.mean(energies):.2f} J")

    # Step 6 - Save & visualize
    df = pd.DataFrame(all_records)
    df.to_csv("data/workload_results.csv", index=False)
    plot_latency_by_app(df)

    safe_print("\n[OK] Outputs generated:", fallback="\n[OK] Outputs generated:")
    print("data/workload_results.csv")
    print("data/workload_comparison.png")


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
