# main.py
from orchestrator.environment import Task, Node
from orchestrator.base_orchestrator import RandomOrchestrator
from orchestrator.rule_orchestrator import RuleBasedOrchestrator
from orchestrator.rl_orchestrator import RLBasedOrchestrator
from orchestrator.simulation import NetworkSimulator
from orchestrator.workload_generator import WorkloadGenerator
import pandas as pd
import matplotlib.pyplot as plt

def run_with_workload():
    # Step 1 – Generate or load workload
    gen = WorkloadGenerator(num_tasks=300)
    gen.generate()

    df_work = pd.read_csv("data/workloads.csv")
    sim = NetworkSimulator()
    all_records = []

    def make_nodes():
        return Node("Edge", 5, 2.0), Node("Cloud", 20, 8.0)

    strategies = {
        "Random": RandomOrchestrator,
        "Rule": RuleBasedOrchestrator,
        "RL": RLBasedOrchestrator,
    }

    for name, OrchClass in strategies.items():
        edge, cloud = make_nodes()
        if name == "RL":
            orch = OrchClass(edge, cloud, episodes=200)
            orch.simulate_environment()
        else:
            orch = OrchClass(edge, cloud)

        latencies = []
        for _, row in df_work.iterrows():
            task = Task(int(row.task_id), float(row.size_mb), row.priority)
            if name == "RL":
                node_name, latency = orch.assign_task(task)
            elif name == "Rule":
                node = orch.edge if (task.size_mb < 5 or task.priority == "high") else orch.cloud
                latency = node.execute_task(task, network_sim=sim)
                node_name = node.name
            else:  # Random
                node = OrchClass(edge, cloud).edge if (name=="Random" and row.task_id%2==0) else cloud
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
        print(f"✅ {name} done | avg latency: {sum(latencies)/len(latencies):.2f} ms")

    df = pd.DataFrame(all_records)
    df.to_csv("data/workload_results.csv", index=False)
    plot_latency_by_app(df)

def plot_latency_by_app(df):
    import matplotlib.pyplot as plt
    import seaborn as sns


    plt.close('all')

    # 🔹 Create a colored boxplot using seaborn
    plt.figure(figsize=(9,6))
    sns.boxplot(
        x="app_type", 
        y="latency", 
        hue="strategy", 
        data=df,
        palette="Set2"   # soft color theme
    )

    plt.title("Latency Comparison per App Type & Strategy")
    plt.ylabel("Latency (ms)")
    plt.xlabel("Application Type")
    plt.legend(title="Strategy")
    plt.xticks(rotation=15)
    plt.tight_layout()

    # 🔹 Save and display
    plt.savefig("data/workload_comparison.png")
    plt.show()

if __name__ == "__main__":
    run_with_workload()
