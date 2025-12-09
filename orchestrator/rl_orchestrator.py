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



# ---------------------------------------------------------------------
# Feature Extractor for AQL
# ---------------------------------------------------------------------
class FeatureExtractor:
    """
    extracts features from state-action pairs for Linear Function Approximation.
    Features:
    1. Bias
    2. Scaled Latency Estimate (based on node type)
    3. Scaled Load
    4. Task Size (scaled)
    5. Priority (one-hot or scaled)
    """
    def get_features(self, state: tuple, action: int, cloud_idx: int = 1) -> np.ndarray:
        # State: (app_type, priority, size_category, load_category, raw_size, raw_load)
        # We need raw values for better approximation, so we'll adjust _get_state first.
        # However, to keep signature compatible, we'll parse the tuple or expect enhanced state.
        
        # Unpack simplified state for now (assuming we update _get_state to return raw vals too)
        # For this implementation, we will assume state contains:
        # (app_type_idx, priority_idx, size_mb, current_load_norm)
        
        app_idx, prio_idx, size_mb, load_norm = state
        
        # Feature vector size: 6
        # [Bias, Is_Cloud, Size, Load, Size*Load, Priority]
        features = np.zeros(6)
        
        features[0] = 1.0 # Bias
        features[1] = 1.0 if action == cloud_idx else 0.0
        features[2] = size_mb / 10.0 # Scale
        features[3] = load_norm
        features[4] = (size_mb / 10.0) * load_norm # Interaction term
        features[5] = prio_idx / 2.0 # 0, 0.5, 1.0
        
        return features

class RLBasedOrchestrator:
    """"
    UPGRADE: Approximate Q-Learning (AQL) with Linear Function Approximation.
    Objectives: Minimize Latency AND Energy.
    """

    def __init__(
        self,
        edge: Optional[Node] = None,
        cloud: Optional[Node] = None,
        *,
        sim: Optional[NetworkSimulator] = None,
        episodes: int = 200,
        epsilon: float = 0.3,
        alpha: float = 0.01, # Smaller alpha for AQL
        gamma: float = 0.9,
    ):
        # Default edge/cloud nodes
        self.edge = edge or Node(0, "edge", 2.0)
        self.cloud = cloud or Node(1, "cloud", 8.0)

        # Simulator injection
        self.sim = sim or NetworkSimulator()

        # Q-learning parameters
        self.episodes = episodes
        self.epsilon = epsilon
        self.alpha = alpha
        self.gamma = gamma
        
        # AQL: Weights vector instead of Q-Table
        # Features: 6 dimensions
        self.weights = np.zeros(6)
        self.feature_extractor = FeatureExtractor()

        # Reward weights
        # Reward weights - Tuned for Latency Reduction
        self.w_latency = 5.0
        self.w_energy = 0.1

    # -----------------------------
    # Simulator setter (for main.py)
    # -----------------------------
    def set_simulator(self, sim):
        """Attach or replace the simulator dynamically."""
        self.sim = sim

    def _get_state_raw(self, task: Task, edge_load: float, cloud_load: float) -> tuple:
        """
        Returns raw state values for feature extraction.
        (app_idx, prio_idx, size_mb, load_norm)
        """
        app_map = {"iot": 0, "arvr": 1, "vanet": 2}
        prio_map = {"low": 0, "medium": 1, "high": 2}
        
        app_idx = app_map.get(task.app_type.lower(), 0)
        prio_idx = prio_map.get(task.priority.lower(), 0)
        
        avg_load = (edge_load + cloud_load) / 2.0
        load_norm = min(1.0, max(0.0, avg_load / 100.0))
        
        return (app_idx, prio_idx, task.size_mb, load_norm)

    def _get_q(self, state: tuple, action: int) -> float:
        features = self.feature_extractor.get_features(state, action)
        return np.dot(self.weights, features)

    def _get_state(self, task: Task, edge_load: float = 0.0, cloud_load: float = 0.0) -> tuple:
        # Legacy support wrapper if needed, but we use raw mostly
        return self._get_state_raw(task, edge_load, cloud_load)

    # ------------------------------------------------------------------
    # Core interaction
    # ------------------------------------------------------------------
    def assign_and_execute(self, task: Task, action: int) -> Tuple[str, float, float]:
        """
        Executes the task. Returns (node_name, latency_ms, energy_joules).
        """
        node = self.edge if action == 0 else self.cloud
        # Updated execute_task returns (latency, energy)
        latency, energy = node.execute_task(task, network_sim=self.sim)
        return (node.name, latency, energy)

    def choose_action(self, state: tuple) -> int:
        """ε-greedy policy."""
        if random.random() < self.epsilon:
            return random.choice([0, 1])
        q_edge = self._get_q(state, 0)
        q_cloud = self._get_q(state, 1)
        return 0 if q_edge >= q_cloud else 1

    def choose_action_greedy(self, state: tuple) -> int:
        """Greedy policy (always exploit) for evaluation."""
        q_edge = self._get_q(state, 0)
        q_cloud = self._get_q(state, 1)
        return 0 if q_edge >= q_cloud else 1

    def update_q(self, state: tuple, action: int, reward: float, next_state: tuple):
        """AQL Gradient Descent Update."""
        # Target = R + gamma * max_a(Q(s', a))
        q_next_max = max(self._get_q(next_state, a) for a in [0, 1])
        target = reward + self.gamma * q_next_max
        
        # Prediction = Q(s, a)
        prediction = self._get_q(state, action)
        
        # Error
        td_error = target - prediction
        
        # Gradient Update: w <- w + alpha * error * features
        features = self.feature_extractor.get_features(state, action)
        self.weights += self.alpha * td_error * features

    # ------------------------------------------------------------------
    # Training loop
    # ------------------------------------------------------------------
    def simulate_environment(self, num_tasks: int = 300):
        """Runs AQL training."""
        safe_print("[START] Starting AQL Simulation (Proposal Aligned)...", fallback="[START] Starting AQL Simulation...")
        total_rewards: list[float] = []

        for ep in range(self.episodes):
            episode_reward = 0.0
            self.edge.reset_load()
            self.cloud.reset_load()
            
            for i in range(num_tasks):
                # Generate Task - Aligned with WorkloadGenerator
                app = random.choice(["IoT", "ARVR", "VANET"])
                prio_map = {"IoT": ["low"]*6 + ["medium"]*3 + ["high"]*1,
                           "ARVR": ["low"]*2 + ["medium"]*5 + ["high"]*3,
                           "VANET": ["low"]*3 + ["medium"]*5 + ["high"]*2}
                prio = random.choice(prio_map[app])
                
                # Size ranges from report
                if app == "IoT": size = random.uniform(0.5, 3.0)
                elif app == "ARVR": size = random.uniform(5.0, 12.0)
                else: size = random.uniform(2.0, 8.0)
                
                task = Task(i, app, round(size, 3), prio)

                state = self._get_state_raw(task, self.edge.current_load, self.cloud.current_load)
                action = self.choose_action(state)
                
                # Execute
                _, latency, energy = self.assign_and_execute(task, action)

                # Reward: Multi-objective (Latency + Energy)
                # Normalize values roughly: Latency in ms (~10-100), Energy in J (~0.1-5)
                # Reward = - (Latency/100 + Energy)
                reward = - ( (latency / 100.0) * self.w_latency + energy * self.w_energy )
                
                # Next State
                next_app = random.choice(["IoT", "ARVR", "VANET"])
                if next_app == "IoT": next_size = random.uniform(0.5, 3.0)
                elif next_app == "ARVR": next_size = random.uniform(5.0, 12.0)
                else: next_size = random.uniform(2.0, 8.0)
                next_prio = random.choice(prio_map[next_app])
                
                next_task = Task(i+1, next_app, round(next_size, 3), next_prio)
                next_state = self._get_state_raw(next_task, self.edge.current_load, self.cloud.current_load)
                
                self.update_q(state, action, reward, next_state)
                episode_reward += reward

            total_rewards.append(episode_reward)
            self.epsilon = max(0.05, self.epsilon * 0.99)

            if (ep + 1) % 20 == 0:
                avg_r = np.mean(total_rewards[-20:])
                print(f"Episode {ep+1:3d}/{self.episodes} | Avg reward (last 20): {avg_r:.2f}")

        safe_print("[OK] AQL training completed.", fallback="[OK] AQL training completed.")
        return 0, total_rewards # Return dummy latency for signature compat

    # ------------------------------------------------------------------
    # Persistence utilities
    # ------------------------------------------------------------------
    def save_weights(self, path: str) -> None:
        np.save(path, self.weights, allow_pickle=True)
        safe_print(f"[SAVE] Saved AQL weights -> {path}", fallback=f"[SAVE] Saved AQL weights -> {path}")

    def load_weights(self, path: str) -> bool:
        try:
            self.weights = np.load(path, allow_pickle=True)
            safe_print(f"[LOAD] Loaded AQL weights from {path}", fallback=f"[LOAD] Loaded AQL weights from {path}")
            return True
        except Exception:
            return False

def get_simulator(sim_type: str) -> NetworkSimulator:
    """Factory to get the desired simulator instance."""
    from orchestrator.sim_interface import get_simulator as factory_get
    return factory_get(sim_type)