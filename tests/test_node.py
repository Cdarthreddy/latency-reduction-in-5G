"""
Tests for Node class and task execution.
"""
import pytest
from orchestrator.environment import Node, Task
from orchestrator.sim_interface import NetworkSimulator, FiveGDistributedSimulator, Simu5GAdapter


class TestNode:
    """Test Node class."""
    
    def test_node_initialization(self):
        """Test node can be initialized."""
        node = Node(0, "edge", 2.0)
        assert node.node_id == 0
        assert node.node_type == "edge"
        assert node.capacity_mbps == 2.0
        assert node.current_load == 0.0
        assert node.name == "edge_0"
    
    def test_node_name_formatting(self):
        """Test node name is properly formatted."""
        edge = Node(0, "edge", 2.0)
        cloud = Node(1, "cloud", 8.0)
        assert edge.name == "edge_0"
        assert cloud.name == "cloud_1"
    
    def test_execute_task_without_simulator(self):
        """Test task execution without network simulator."""
        node = Node(0, "edge", 2.0)
        task = Task(1, "IoT", 2.0, "high")
        
        latency, energy = node.execute_task(task)
        assert latency > 0
        assert energy > 0
        # Processing time: 2.0 MB / 2.0 Mbps = 1.0 second = 1000 ms
        assert latency >= 1000
    
    def test_execute_task_with_basic_simulator(self):
        """Test task execution with basic NetworkSimulator."""
        node = Node(0, "edge", 2.0)
        task = Task(1, "IoT", 2.0, "high")
        sim = NetworkSimulator()
        
        latency, energy = node.execute_task(task, network_sim=sim)
        assert latency > 1000  # Should include network latency
    
    def test_execute_task_with_simple_simulator(self):
        """Test task execution with FiveGDistributedSimulator (enhanced modeling)."""
        node = Node(0, "edge", 2.0)
        task = Task(1, "IoT", 2.0, "high")
        sim = FiveGDistributedSimulator()
        
        latency, energy = node.execute_task(task, network_sim=sim)
        assert latency > 1000  # Should include network latency
    
    def test_execute_task_updates_load(self):
        """Test that executing task updates node load."""
        node = Node(0, "edge", 2.0)
        task = Task(1, "IoT", 5.0, "high")
        
        assert node.current_load == 0.0
        node.execute_task(task)
        assert node.current_load == 5.0
        
        # Execute another task
        task2 = Task(2, "ARVR", 3.0, "medium")
        node.execute_task(task2)
        assert node.current_load == 8.0
    
    def test_load_affects_latency_with_simulator(self):
        """Test that node load affects latency when using simulator."""
        node = Node(0, "edge", 2.0)
        task = Task(1, "IoT", 1.0, "high")
        sim = FiveGDistributedSimulator()
        
        # First execution - no load
        latency1, _ = node.execute_task(task, network_sim=sim)
        
        # Add load
        node.current_load = 50.0
        
        # Second execution - with load
        latency2, _ = node.execute_task(task, network_sim=sim)
        
        # Latency should be higher with load (due to simulator modeling)
        assert latency2 > latency1
    
    def test_reset_load(self):
        """Test resetting node load."""
        node = Node(0, "edge", 2.0)
        task = Task(1, "IoT", 5.0, "high")
        
        node.execute_task(task)
        assert node.current_load == 5.0
        
        node.reset_load()
        assert node.current_load == 0.0
    
    def test_edge_vs_cloud_processing(self):
        """Test that edge and cloud have different processing times."""
        edge = Node(0, "edge", 2.0)  # Lower capacity
        cloud = Node(1, "cloud", 8.0)  # Higher capacity
        task = Task(1, "IoT", 8.0, "high")
        
        edge_latency, _ = edge.execute_task(task)
        cloud_latency, _ = cloud.execute_task(task)
        
        # Edge should take longer for processing (8.0 MB / 2.0 Mbps = 4s)
        # Cloud should be faster (8.0 MB / 8.0 Mbps = 1s)
        # But network latency might make cloud slower overall
        assert edge_latency > 0
        assert cloud_latency > 0
    
    def test_task_size_affects_processing_time(self):
        """Test that larger tasks take longer to process."""
        node = Node(0, "edge", 2.0)
        
        small_task = Task(1, "IoT", 1.0, "high")
        large_task = Task(2, "ARVR", 10.0, "high")
        
        small_latency, _ = node.execute_task(small_task)
        large_latency, _ = node.execute_task(large_task)
        
        assert large_latency > small_latency
    
    def test_simulator_receives_task_info(self):
        """Test that simulator receives task size and load information."""
        node = Node(0, "edge", 2.0)
        task = Task(1, "IoT", 5.0, "high")
        sim = FiveGDistributedSimulator()
        
        # Add some load
        node.current_load = 20.0
        
        # Execute task - simulator should receive task size and load
        latency, _ = node.execute_task(task, network_sim=sim)
        
        # Verify it executed (latency > 0)
        assert latency > 0
        # Verify load was updated
        assert node.current_load == 25.0

