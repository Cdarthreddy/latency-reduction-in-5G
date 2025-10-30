from orchestrator.environment import Node, Task
from orchestrator.rl_agent import RLAgent
import random
import os
import numpy as np

class RLBasedOrchestrator:
    def __init__(self, edge_node, cloud_node, episodes=1000):
        self.edge = edge_node
        self.cloud = cloud_node
        self.agent = RLAgent()
        self.episodes = episodes
        # 🔹 load pretrained weights if available
        weights_path = "data/rl_weights.npy"
        if os.path.exists(weights_path):
            self.agent.weights = np.load(weights_path)
            print("🔹 Loaded pretrained RL weights")

    def simulate_environment(self):
        """Run RL training episodes."""
        rewards = []
        for _ in range(self.episodes):
            # random starting conditions
            state = [
                random.uniform(2, 15),   # edge latency
                random.uniform(15, 35),  # cloud latency
                self.edge.current_load,
                random.uniform(1, 10)    # task size
            ]
            action = self.agent.choose_action(state)

            # Execute chosen action
            task = Task(task_id=0, size_mb=state[3], priority="medium")
            node = self.edge if action == 0 else self.cloud
            latency = node.execute_task(task)

            reward = -latency  # smaller latency = higher reward

            # next state after task execution
            next_state = [
                random.uniform(2, 15),
                random.uniform(15, 35),
                self.edge.current_load,
                random.uniform(1, 10)
            ]
            self.agent.update(state, action, reward, next_state)
            rewards.append(reward)
        return rewards

    def assign_task(self, task: Task):
        """Use trained agent to decide placement."""
        state = [
            random.uniform(2, 15),
            random.uniform(15, 35),
            self.edge.current_load,
            task.size_mb
        ]
        action = self.agent.choose_action(state)
        node = self.edge if action == 0 else self.cloud
        latency = node.execute_task(task)
        return node.name, latency
