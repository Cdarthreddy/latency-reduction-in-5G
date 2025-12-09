import os
from orchestrator.environment import Node
from orchestrator.rl_orchestrator import RLBasedOrchestrator
from orchestrator.sim_interface import get_simulator
import numpy as np

def ensure_dirs():
    """Ensures the data directory exists."""
    os.makedirs("data", exist_ok=True)

def train_and_eval(episodes: int = 1000, sim_type: str = "simple"):
    """
    Train the RL orchestrator and return average latency.
    Used by main_remote.py for AWS deployment.
    
    Args:
        episodes (int): Number of training episodes.
        sim_type (str): Type of simulator to use ('simple' or 'fiveg').
        
    Returns:
        float: Average latency from final evaluation
    """
    print(f"--- Starting RL Training for Latency Reduction (Sim: {sim_type}, Episodes: {episodes}) ---")
    
    # Ensure data directory exists
    ensure_dirs()
    
    # Setup Environment
    edge = Node(0, "edge", 2.0)
    cloud = Node(1, "cloud", 8.0)
    
    # Use specified simulator
    sim = get_simulator(sim_type)
    
    # Initialize Agent
    # Increased episodes for better convergence on new policy
    orch = RLBasedOrchestrator(edge, cloud, episodes=episodes, alpha=0.1, epsilon=0.5)
    orch.set_simulator(sim)
    
    # Train
    latencies, rewards = orch.simulate_environment(num_tasks=300)
    
    # Save Weights
    orch.save_weights("data/rl_weights.npy")
    
    avg_latency = np.mean(latencies) if latencies else 0.0
    print(f"Training Complete. Final Avg Reward: {np.mean(rewards[-50:]):.4f}")
    
    return avg_latency

def train():
    """Backward compatibility wrapper for direct script execution."""
    train_and_eval()

if __name__ == "__main__":
    train()
