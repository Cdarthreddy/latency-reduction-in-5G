"""
Tests for network simulator implementations.
"""
import pytest
import numpy as np
from orchestrator.sim_interface import NetworkSimulator, SimpleSimulator, Simu5GAdapter, get_simulator
from orchestrator.environment import Task, Node


class TestNetworkSimulator:
    """Test base NetworkSimulator class."""
    
    def test_basic_simulator_initialization(self):
        """Test basic simulator can be initialized."""
        sim = NetworkSimulator()
        assert sim.base_edge_latency == 0.002
        assert sim.base_cloud_latency == 0.008
    
    def test_basic_simulate_latency(self):
        """Test basic simulate_latency method."""
        sim = NetworkSimulator()
        latency = sim.simulate_latency("edge", "IoT")
        assert latency > 0
        assert isinstance(latency, float)
    
    def test_edge_vs_cloud_latency(self):
        """Test edge has lower latency than cloud."""
        sim = NetworkSimulator()
        edge_lat = sim.simulate_latency("edge", "IoT")
        cloud_lat = sim.simulate_latency("cloud", "IoT")
        assert edge_lat < cloud_lat


class TestSimpleSimulator:
    """Test SimpleSimulator implementation."""
    
    def test_simple_simulator_initialization(self):
        """Test SimpleSimulator can be initialized."""
        sim = SimpleSimulator()
        assert sim.base_edge_ms == 5.0
        assert sim.base_cloud_ms == 25.0
    
    def test_simulate_latency_override(self):
        """Test that simulate_latency is properly overridden."""
        sim = SimpleSimulator()
        # Should use advanced modeling, not basic parent method
        latency = sim.simulate_latency("edge", "IoT", task_size_mb=1.0, node_load=0.0)
        assert latency > 0
        # Should be in seconds (converted from ms)
        assert latency < 1.0  # Should be milliseconds converted to seconds
    
    def test_latency_ms_method(self):
        """Test latency_ms method directly."""
        sim = SimpleSimulator()
        latency = sim.latency_ms("edge", load=0.0, task_size_mb=1.0)
        assert latency > 0
        assert isinstance(latency, float)
    
    def test_load_affects_latency(self):
        """Test that higher load increases latency."""
        sim = SimpleSimulator()
        low_load = sim.simulate_latency("edge", "IoT", task_size_mb=1.0, node_load=0.0)
        high_load = sim.simulate_latency("edge", "IoT", task_size_mb=1.0, node_load=50.0)
        assert high_load > low_load
    
    def test_task_size_affects_latency(self):
        """Test that larger tasks have higher latency (on average)."""
        sim = SimpleSimulator()
        
        # Run multiple samples to account for random noise
        small_latencies = []
        large_latencies = []
        
        for _ in range(10):
            small_latencies.append(sim.simulate_latency("edge", "IoT", task_size_mb=0.5, node_load=0.0))
            large_latencies.append(sim.simulate_latency("edge", "IoT", task_size_mb=10.0, node_load=0.0))
        
        # Check that on average, larger tasks have higher latency
        avg_small = np.mean(small_latencies)
        avg_large = np.mean(large_latencies)
        
        assert avg_large > avg_small, f"Average latency for large task ({avg_large:.6f}) should be > small task ({avg_small:.6f})"


class TestSimu5GAdapter:
    """Test Simu5GAdapter implementation."""
    
    def test_simu5g_adapter_initialization(self):
        """Test Simu5GAdapter can be initialized."""
        sim = Simu5GAdapter()
        assert sim.endpoint == "localhost:5555"
    
    def test_simulate_latency_override(self):
        """Test that simulate_latency is properly overridden."""
        sim = Simu5GAdapter(simulate_delay=False)  # Disable delay for faster tests
        latency = sim.simulate_latency("edge", "IoT", task_size_mb=1.0, node_load=0.0)
        assert latency > 0
        assert latency < 1.0  # Should be in seconds


class TestSimulatorFactory:
    """Test simulator factory function."""
    
    def test_get_simple_simulator(self):
        """Test getting SimpleSimulator from factory."""
        sim = get_simulator("simple")
        assert isinstance(sim, SimpleSimulator)
    
    def test_get_simu5g_simulator(self):
        """Test getting Simu5GAdapter from factory."""
        sim = get_simulator("simu5g")
        assert isinstance(sim, Simu5GAdapter)
    
    def test_invalid_simulator_name(self):
        """Test that invalid simulator name raises error."""
        with pytest.raises(ValueError):
            get_simulator("invalid")


class TestNodeWithSimulator:
    """Test Node integration with simulators."""
    
    def test_node_execute_task_with_simple_simulator(self):
        """Test Node.execute_task works with SimpleSimulator."""
        node = Node(0, "edge", 2.0)
        task = Task(1, "IoT", 1.0, "high")
        sim = SimpleSimulator()
        
        latency = node.execute_task(task, network_sim=sim)
        assert latency > 0
        # Latency should include both processing and network delay
        assert latency > 100  # Should be in milliseconds
    
    def test_node_load_affects_latency(self):
        """Test that node load affects latency through simulator."""
        node = Node(0, "edge", 2.0)
        task = Task(1, "IoT", 1.0, "high")
        sim = SimpleSimulator()
        
        # First task - no load
        latency1 = node.execute_task(task, network_sim=sim)
        
        # Add some load
        node.current_load = 50.0
        
        # Second task - with load
        latency2 = node.execute_task(task, network_sim=sim)
        
        # Latency should be higher with load
        assert latency2 > latency1

