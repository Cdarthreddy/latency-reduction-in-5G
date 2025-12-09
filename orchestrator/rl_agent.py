# orchestrator/rl_agent.py
import numpy as np
import random

class RLAgent:
    """
    Approximate Q-Learning agent for Edge/Cloud task placement.
    """

    def __init__(self, learning_rate=0.1, discount_factor=0.9, epsilon=0.2):
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon  # exploration probability
        # weights for features (initialized small)
        self.weights = np.random.uniform(-0.1, 0.1, 4)  # 4 input features

    def featurize(self, state):
        """
        Convert raw state to numeric feature vector.
        state = [latency_edge, latency_cloud, edge_load, task_size]
        """
        latency_edge, latency_cloud, edge_load, task_size = state
        return np.array([
            latency_edge / 50.0,
            latency_cloud / 50.0,
            edge_load,
            task_size / 10.0
        ])

    def predict_q(self, features):
        """Compute Q-value approximation for both actions."""
        # linear approximation: Q = w·x for each action (Edge vs Cloud)
        return np.dot(self.weights, features)

    def choose_action(self, state):
        """ε-greedy policy."""
        if random.random() < self.epsilon:
            return random.choice([0, 1])  # explore
        q_edge = self.q_value(state, 0)
        q_cloud = self.q_value(state, 1)
        return 0 if q_edge > q_cloud else 1  # exploit

    def q_value(self, state, action):
        """Return predicted Q for the given action."""
        features = self.featurize(state)
        # Add simple action bias: if cloud, shift slightly
        if action == 1:
            features = features * 1.1
        return self.predict_q(features)

    def update(self, state, action, reward, next_state):
        """Q-learning weight update."""
        features = self.featurize(state)
        current_q = self.q_value(state, action)
        next_q_edge = self.q_value(next_state, 0)
        next_q_cloud = self.q_value(next_state, 1)
        target = reward + self.gamma * max(next_q_edge, next_q_cloud)
        td_error = target - current_q
        self.weights += self.lr * td_error * features
