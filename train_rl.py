# train_rl.py
from orchestrator.environment import Node, Task
from orchestrator.rl_orchestrator import RLBasedOrchestrator
import numpy as np

def train_rl_agent():
    edge = Node("Edge", 5, 2.0)
    cloud = Node("Cloud", 20, 8.0)
    rl_orch = RLBasedOrchestrator(edge, cloud, episodes=1500)
    rewards = rl_orch.simulate_environment()
    np.save("data/rl_weights.npy", rl_orch.agent.weights)
    print("✅ RL agent trained & weights saved → data/rl_weights.npy")

if __name__ == "__main__":
    train_rl_agent()
