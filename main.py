# main.py
from orchestrator.environment import Task, Node
from orchestrator.base_orchestrator import RandomOrchestrator
from orchestrator.rule_orchestrator import RuleBasedOrchestrator
from orchestrator.rl_orchestrator import RLBasedOrchestrator
from orchestrator.simulation import NetworkSimulator
import pandas as pd
import random
import matplotlib.pyplot as plt

def run_comparison(num_tasks=100):
    sim = NetworkSimulator()
    all_records = []

    def make_nodes():
        return Node("Edge", 5, 2.0), Node("Cloud", 20, 8.0)

    # Instantiate each orchestrator
    strategies = {
        "Random": RandomOrchestrator,
        "Rule": RuleBasedOrchestrator,
        "RL": RLBasedOrchestrator,
    }

    for name, orch_class in strategies.items():
        edge, cloud = make_nodes()
        if name == "RL":
            orch = orch_class(edge, cloud, episodes=200)
            orch.simulate_environment()  # pre-train RL agent
        else:
            orch = orch_class(edge, cloud)

        latencies = []
        for i in range(num_tasks):
            task = Task(i, random.uniform(1, 10), random.choice(["high", "medium", "low"]))
            if name == "RL":
                node_name, latency = orch.assign_task(task)
            else:
                node = orch.edge if name == "Rule" and (task.size_mb < 5 or task.priority == "high") else random.choice([orch.edge, orch.cloud])
                latency = node.execute_task(task, network_sim=sim)
                node_name = node.name
            all_records.append({"strategy": name, "node": node_name, "latency": latency})
            latencies.append(latency)
        print(f"✅ {name} orchestrator avg latency: {sum(latencies)/len(latencies):.2f} ms")

    df = pd.DataFrame(all_records)
    df.to_csv("data/combined_results.csv", index=False)
    plot_results(df)

def plot_results(df):
    plt.figure(figsize=(8,5))
    df.boxplot(column="latency", by="strategy", grid=True)
    plt.title("Latency Comparison (Edge + Cloud Simulation)")
    plt.suptitle("")  # remove extra header
    plt.ylabel("Latency (ms)")
    plt.savefig("data/combined_boxplot.png")
    plt.show()

if __name__ == "__main__":
    run_comparison()
