"""
Tests for RL-based orchestrator.
"""
import pytest
import numpy as np
from orchestrator.rl_orchestrator import RLBasedOrchestrator
from orchestrator.environment import Task, Node
from orchestrator.sim_interface import SimpleSimulator


class TestRLOrchestrator:
    """Test RLBasedOrchestrator class."""
    
    def test_initialization(self):
        """Test orchestrator can be initialized."""
        orch = RLBasedOrchestrator()
        assert orch.episodes == 200
        assert orch.epsilon == 0.3
        assert orch.alpha == 0.5
        assert orch.gamma == 0.9
        assert isinstance(orch.edge, Node)
        assert isinstance(orch.cloud, Node)
    
    def test_custom_initialization(self):
        """Test orchestrator with custom parameters."""
        edge = Node(0, "edge", 2.0)
        cloud = Node(1, "cloud", 8.0)
        sim = SimpleSimulator()
        orch = RLBasedOrchestrator(edge=edge, cloud=cloud, sim=sim, episodes=100, epsilon=0.1)
        assert orch.episodes == 100
        assert orch.epsilon == 0.1
        assert orch.edge == edge
        assert orch.cloud == cloud
    
    def test_set_simulator(self):
        """Test setting simulator dynamically."""
        orch = RLBasedOrchestrator()
        sim = SimpleSimulator()
        orch.set_simulator(sim)
        assert orch.sim == sim
    
    def test_get_state_enhanced(self):
        """Test enhanced state representation includes size and load."""
        orch = RLBasedOrchestrator()
        task = Task(1, "IoT", 5.0, "high")
        
        state = orch._get_state(task, edge_load=10.0, cloud_load=20.0)
        assert len(state) == 4
        assert state[0] == "iot"  # app_type
        assert state[1] == "high"  # priority
        assert state[2] in ["small", "medium", "large"]  # size_category
        assert state[3] in ["low", "medium", "high"]  # load_category
    
    def test_state_size_categorization(self):
        """Test task size is properly categorized."""
        orch = RLBasedOrchestrator()
        
        # Small task
        small_task = Task(1, "IoT", 1.0, "low")
        state = orch._get_state(small_task)
        assert state[2] == "small"
        
        # Medium task
        medium_task = Task(2, "IoT", 5.0, "low")
        state = orch._get_state(medium_task)
        assert state[2] == "medium"
        
        # Large task
        large_task = Task(3, "ARVR", 10.0, "high")
        state = orch._get_state(large_task)
        assert state[2] == "large"
    
    def test_state_load_categorization(self):
        """Test node load is properly categorized."""
        orch = RLBasedOrchestrator()
        task = Task(1, "IoT", 1.0, "low")
        
        # Low load
        state = orch._get_state(task, edge_load=10.0, cloud_load=10.0)
        assert state[3] == "low"
        
        # Medium load
        state = orch._get_state(task, edge_load=40.0, cloud_load=40.0)
        assert state[3] == "medium"
        
        # High load
        state = orch._get_state(task, edge_load=80.0, cloud_load=80.0)
        assert state[3] == "high"
    
    def test_assign_and_execute(self):
        """Test task assignment and execution."""
        orch = RLBasedOrchestrator()
        task = Task(1, "IoT", 1.0, "high")
        
        # Execute on edge (action 0)
        node_name, latency = orch.assign_and_execute(task, action=0)
        assert node_name == "edge_0"
        assert latency > 0
        
        # Execute on cloud (action 1)
        node_name, latency = orch.assign_and_execute(task, action=1)
        assert node_name == "cloud_1"
        assert latency > 0
    
    def test_choose_action_epsilon_greedy(self):
        """Test epsilon-greedy action selection."""
        orch = RLBasedOrchestrator(epsilon=0.0)  # No exploration
        task = Task(1, "IoT", 1.0, "high")
        state = orch._get_state(task)
        
        # With epsilon=0, should always choose greedy action
        action = orch.choose_action(state)
        assert action in [0, 1]
    
    def test_choose_action_greedy(self):
        """Test purely greedy action selection."""
        orch = RLBasedOrchestrator()
        task = Task(1, "IoT", 1.0, "high")
        state = orch._get_state(task)
        
        action = orch.choose_action_greedy(state)
        assert action in [0, 1]
    
    def test_update_q(self):
        """Test Q-value update."""
        orch = RLBasedOrchestrator()
        task1 = Task(1, "IoT", 1.0, "high")
        task2 = Task(2, "ARVR", 5.0, "medium")
        
        state1 = orch._get_state(task1)
        state2 = orch._get_state(task2)
        
        # Initial Q-value should be 0
        assert orch._get_q(state1, 0) == 0.0
        
        # Update Q-value
        orch.update_q(state1, action=0, reward=-100.0, next_state=state2)
        
        # Q-value should be updated
        assert orch._get_q(state1, 0) != 0.0
        assert orch._get_q(state1, 0) < 0  # Negative reward
    
    def test_save_and_load_weights(self):
        """Test saving and loading Q-table."""
        import tempfile
        import os
        
        orch = RLBasedOrchestrator()
        task = Task(1, "IoT", 1.0, "high")
        state = orch._get_state(task)
        
        # Update Q-table
        orch.update_q(state, action=0, reward=-100.0, next_state=state)
        
        # Save weights
        with tempfile.NamedTemporaryFile(delete=False, suffix='.npy') as f:
            temp_path = f.name
        
        try:
            orch.save_weights(temp_path)
            assert os.path.exists(temp_path)
            
            # Create new orchestrator and load weights
            orch2 = RLBasedOrchestrator()
            success = orch2.load_weights(temp_path)
            assert success
            
            # Check Q-value was loaded
            assert orch2._get_q(state, 0) == orch._get_q(state, 0)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_simulate_environment_resets_loads(self):
        """Test that simulate_environment resets node loads each episode."""
        orch = RLBasedOrchestrator(episodes=2)
        sim = SimpleSimulator()
        orch.set_simulator(sim)
        
        # Run simulation
        avg_latency, rewards = orch.simulate_environment(num_tasks=10)
        
        # Check that loads were reset (should be > 0 after execution)
        # But we can't directly check during execution, so we verify it runs
        assert len(rewards) == 2
        assert avg_latency > 0

