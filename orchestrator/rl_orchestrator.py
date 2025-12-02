# orchestrator/rl_orchestrator.py
from __future__ import annotations
import random
import numpy as np
from typing import Tuple, Optional

from orchestrator.environment import Task, Node
from orchestrator.sim_interface import NetworkSimulator

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


class RLBasedOrchestrator:
    """
    Week 8 – Reinforcement Learning–based orchestrator.

    Supports pluggable simulators (SimpleSimulator, Simu5GAdapter).
    Uses Q-learning to minimize latency by choosing between edge and cloud nodes.
    """

    def __init__(
        self,
        edge: Optional[Node] = None,
        cloud: Optional[Node] = None,
        *,
        sim: Optional[NetworkSimulator] = None,
        episodes: int = 200,
        epsilon: float = 0.3,
        alpha: float = 0.5,
        gamma: float = 0.9,
    ):
        # Default edge/cloud nodes
        self.edge = edge or Node(0, "edge", 2.0)
        self.cloud = cloud or Node(1, "cloud", 8.0)

        # Simulator injection (simple or simu5g)
        self.sim = sim or NetworkSimulator()

        # Q-learning parameters
        self.episodes = episodes
        self.epsilon = epsilon
        self.alpha = alpha
        self.gamma = gamma

        # Internal Q-table: {(state, action): value}
        # State format: (app_type, priority, size_category, load_category)
        self.q_table: dict[tuple[tuple, int], float] = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
        # -----------------------------
    # Simulator setter (for main.py)
    # -----------------------------
    def set_simulator(self, sim):
        """Attach or replace the simulator dynamically."""
        self.sim = sim

    def _get_state(self, task: Task, edge_load: float = 0.0, cloud_load: float = 0.0) -> tuple:
        """
        Represent state as (app_type, priority, size_category, load_category).
        
        Enhanced state representation includes:
        - app_type: Application type (iot, arvr, vanet)
        - priority: Task priority (low, medium, high)
        - size_category: Task size category (small, medium, large)
        - load_category: Node load category (low, medium, high)
        """
        app_type = task.app_type.lower()
        priority = task.priority.lower()
        
        # Categorize task size
        if task.size_mb < 2.0:
            size_category = "small"
        elif task.size_mb < 8.0:
            size_category = "medium"
        else:
            size_category = "large"
        
        # Determine which node's load to use (will be set based on action)
        # For now, use average load as approximation
        avg_load = (edge_load + cloud_load) / 2.0
        # Normalize load (assuming max capacity of 100MB)
        normalized_load = min(1.0, max(0.0, avg_load / 100.0))
        
        # Categorize load
        if normalized_load < 0.33:
            load_category = "low"
        elif normalized_load < 0.67:
            load_category = "medium"
        else:
            load_category = "high"
        
        return (app_type, priority, size_category, load_category)

    def _get_q(self, state: tuple, action: int) -> float:
        return self.q_table.get((state, action), 0.0)

    def _set_q(self, state: tuple, action: int, value: float):
        self.q_table[(state, action)] = value

    # ------------------------------------------------------------------
    # Core interaction
    # ------------------------------------------------------------------
    def assign_and_execute(self, task: Task, action: int) -> Tuple[str, float]:
        """
        Executes the task on either edge (action 0) or cloud (action 1).
        Returns (node_name, latency_ms).
        """
        node = self.edge if action == 0 else self.cloud
        latency = node.execute_task(task, network_sim=self.sim)
        return (node.name, latency)

    def choose_action(self, state: tuple) -> int:
        """ε-greedy policy."""
        if random.random() < self.epsilon:
            return random.choice([0, 1])
        q_edge = self._get_q(state, 0)
        q_cloud = self._get_q(state, 1)
        return 0 if q_edge >= q_cloud else 1

    def choose_action_greedy(self, state: tuple) -> int:
        """Purely greedy policy (ε=0) used for evaluation."""
        q_edge = self._get_q(state, 0)
        q_cloud = self._get_q(state, 1)
        return 0 if q_edge >= q_cloud else 1

    def update_q(self, state: tuple, action: int, reward: float, next_state: tuple):
        """Standard Q-learning update."""
        old_q = self._get_q(state, action)
        next_q = max(self._get_q(next_state, a) for a in [0, 1])
        new_q = old_q + self.alpha * (reward + self.gamma * next_q - old_q)
        self._set_q(state, action, new_q)

    # ------------------------------------------------------------------
    # Training loop
    # ------------------------------------------------------------------
    def simulate_environment(self, num_tasks: int = 300):
        """Runs Q-learning episodes using the injected simulator."""
        safe_print("[START] Starting Q-Learning simulation...", fallback="[START] Starting Q-Learning simulation...")
        total_rewards: list[float] = []

        for ep in range(self.episodes):
            episode_reward = 0.0
            # Reset node loads at start of each episode
            self.edge.reset_load()
            self.cloud.reset_load()
            
            for i in range(num_tasks):
                app = random.choice(["IoT", "ARVR", "VANET"])
                prio = random.choice(["high", "medium", "low"])
                size = random.uniform(0.5, 12.0)
                task = Task(i, app, size, prio)

                # Get state with current node loads
                state = self._get_state(task, self.edge.current_load, self.cloud.current_load)
                action = self.choose_action(state)
                _, latency = self.assign_and_execute(task, action)

                # Reward = −latency (minimize delay)
                reward = -latency
                next_task = Task(i + 1,
                                 random.choice(["IoT", "ARVR", "VANET"]),
                                 random.uniform(0.5, 12.0),
                                 random.choice(["high", "medium", "low"]))
                # Get next state with updated node loads
                next_state = self._get_state(next_task, self.edge.current_load, self.cloud.current_load)
                self.update_q(state, action, reward, next_state)

                episode_reward += reward

            total_rewards.append(episode_reward)

            # Decay ε for less exploration over time
            self.epsilon = max(0.05, self.epsilon * 0.99)

            if (ep + 1) % 20 == 0:
                avg_r = np.mean(total_rewards[-20:])
                print(f"Episode {ep+1:3d}/{self.episodes} | Avg reward (last 20): {avg_r:.2f}")

        safe_print("[OK] RL training completed.", fallback="[OK] RL training completed.")
        avg_latency = -np.mean(total_rewards[-10:]) / num_tasks
        safe_print(f"[OK] RL done | avg latency: {avg_latency:.2f} ms", 
                   fallback=f"[OK] RL done | avg latency: {avg_latency:.2f} ms")
        return avg_latency, total_rewards

    # ------------------------------------------------------------------
    # Persistence utilities
    # ------------------------------------------------------------------
    def save_weights(self, path: str) -> None:
        """Save Q-table to .npy file."""
        if not self.q_table:
            safe_print("[WARN] No Q-table to save.", fallback="[WARN] No Q-table to save.")
            return
        arr = np.array(list(self.q_table.items()), dtype=object)
        np.save(path, arr, allow_pickle=True)
        safe_print(f"[SAVE] Saved Q-table -> {path}", fallback=f"[SAVE] Saved Q-table -> {path}")

    def load_weights(self, path: str) -> bool:
        """Load Q-table from .npy file."""
        try:
            arr = np.load(path, allow_pickle=True)
            self.q_table = {tuple(k): v for k, v in arr}
            safe_print(f"[LOAD] Loaded Q-table from {path}", fallback=f"[LOAD] Loaded Q-table from {path}")
            return True
        except Exception as e:
            safe_print(f"[WARN] Could not load Q-table: {e}", fallback=f"[WARN] Could not load Q-table: {e}")
            return False
def get_simulator(sim_type: str) -> NetworkSimulator:
    """Factory to get the desired simulator instance."""
    from orchestrator.simu5g_adapter import Simu5GAdapter

    if sim_type.lower() == "simu5g":
        return Simu5GAdapter()
    else:
        return SimpleSimulator()