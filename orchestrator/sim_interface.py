# orchestrator/sim_interface.py
from __future__ import annotations
import random
import math

# ---------------------------------------------------------------------
# Base abstract simulator
# ---------------------------------------------------------------------
class NetworkSimulator:
    """
    Abstract latency simulator between edge and cloud nodes.
    Produces realistic latency behavior for 5G, Wi-Fi, or backhaul.
    """

    def __init__(self, base_edge_latency=0.002, base_cloud_latency=0.008):
        """
        Latencies are in seconds internally (ms when multiplied by 1000).
        """
        self.base_edge_latency = base_edge_latency
        self.base_cloud_latency = base_cloud_latency

    def simulate_latency(self, node_type: str, app_type: str, task_size_mb: float = 1.0, node_load: float = 0.0) -> float:
        """
        Simulate latency for a given node and app type.
        
        Args:
            node_type: Type of node ("edge" or "cloud")
            app_type: Type of application
            task_size_mb: Size of task in MB (optional, for enhanced simulators)
            node_load: Current load on node in MB (optional, for enhanced simulators)
        
        Returns:
            Latency in seconds
        """
        node = str(node_type).lower()

        # --- base latency ---
        if node in ("edge", "0"):
            base = self.base_edge_latency
        else:
            base = self.base_cloud_latency

        # --- app-specific jitter ---
        app = app_type.upper()
        if app == "IOT":
            jitter = random.uniform(0.0001, 0.0005)
        elif app == "ARVR":
            jitter = random.uniform(0.001, 0.002)
        elif app == "VANET":
            jitter = random.uniform(0.0005, 0.001)
        else:
            jitter = random.uniform(0.0001, 0.001)

        return base + jitter


# ---------------------------------------------------------------------
# Simple built-in simulator
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# Enhanced 5G-Enabled Simulator
# ---------------------------------------------------------------------
class FiveGDistributedSimulator(NetworkSimulator):
    """
    Advanced simulator modeling 5G characteristics including:
    - Path loss and shadowing (log-normal distribution)
    - Interference (SINR modeling)
    - Multipath Fading (Rayleigh/Rician approximation)
    """

    def __init__(
        self,
        base_edge_ms: float = 4.0,  # Improved 5G architecture base
        base_cloud_ms: float = 20.0,
        interference_prob: float = 0.1,
        fading_variance: float = 2.0,
    ):
        super().__init__(base_edge_ms/1000.0, base_cloud_ms/1000.0)
        self.base_edge_ms = base_edge_ms
        self.base_cloud_ms = base_cloud_ms
        self.interference_prob = interference_prob
        self.fading_var = fading_variance

    def _calculate_channel_conditions(self) -> float:
        """
        Simulate channel quality indicator (CQI) effects.
        Returns latency penalty in ms.
        """
        # Multipath fading (Rayleigh approximation for NLOS)
        fading = random.gauss(0, self.fading_var)
        
        # Interference (SINR degradation)
        interference = 0.0
        if random.random() < self.interference_prob:
            # High interference causing packet retransmissions (HARQ)
            interference = random.uniform(5.0, 15.0) 
            
        return max(0.0, fading + interference)

    def latency_ms(self, node_type: str, load: float, task_size_mb: float) -> float:
        t = node_type.lower()
        load = max(0.0, min(1.0, load))
        
        # Channel physical layer effects
        phy_penalty = self._calculate_channel_conditions()
        
        # Transmission delay: Size / Bandwidth (Dynamic based on load)
        # Transmission delay: Size / Bandwidth (Dynamic based on load)
        # 5G Uplink assumption: aligned with proposal (1-20 Mbps) 
        # We use 20.0 Mbps as the peak realistic capacity for this scenario.
        bandwidth_base = 20.0 
        bandwidth_available = bandwidth_base * (1.0 - (0.5 * load)) # Bandwidth shrinks with load
        tx_delay = (task_size_mb * 8) / max(1.0, bandwidth_available) * 1000 # to ms

        if "edge" in t:
            # Edge: Phy effects + Tx delay + Processing queue
            return self.base_edge_ms + tx_delay + phy_penalty + (load * 10.0)

        # Cloud: Backhaul + Core Network delay
        backbone = random.uniform(10, 30)
        return self.base_cloud_ms + backbone + tx_delay + (load * 5.0)

    def simulate_latency(self, node_type: str, app_type: str, task_size_mb: float = 1.0, node_load: float = 0.0) -> float:
        """
        Override parent method to use advanced latency modeling.
        Converts result from milliseconds to seconds for compatibility.
        """
        # Calculate normalized load (0.0 to 1.0)
        # Assuming max capacity of 100MB for normalization
        normalized_load = min(1.0, max(0.0, node_load / 100.0))
        
        # Use the advanced latency_ms method
        latency_ms = self.latency_ms(node_type, normalized_load, task_size_mb)
        
        # Convert from milliseconds to seconds (as expected by Node.execute_task)
        return latency_ms / 1000.0


# ---------------------------------------------------------------------
# Simu5G stub adapter (optional)
# ---------------------------------------------------------------------
class Simu5GAdapter(NetworkSimulator):
    """
    A mock adapter that mimics latency feedback from an external Simu5G instance.
    """

    def __init__(self, endpoint: str | None = None, simulate_delay: bool = True):
        import time
        self.endpoint = endpoint or "localhost:5555"
        self.simulate_delay = simulate_delay
        self._seeded = False
        self._time = time

    def _seed(self):
        if not self._seeded:
            random.seed(self._time.time())
            self._seeded = True

    def latency_ms(self, node_type: str, load: float, task_size_mb: float) -> float:
        self._seed()
        t = node_type.lower()
        base_edge = 4.5
        base_cloud = 22.0
        load_penalty = 25.0 * load
        noise = random.uniform(-1.5, 1.5)
        size_effect = 0.5 * (task_size_mb ** 0.5)

        if "edge" in t:
            latency = base_edge + load_penalty + noise + size_effect
        else:
            backbone = random.uniform(10, 30)
            latency = base_cloud + backbone + load_penalty + noise + size_effect

        if self.simulate_delay:
            self._time.sleep(0.0005)

        return max(1.0, latency)

    def simulate_latency(self, node_type: str, app_type: str, task_size_mb: float = 1.0, node_load: float = 0.0) -> float:
        """
        Override parent method to use Simu5G latency modeling.
        Converts result from milliseconds to seconds for compatibility.
        """
        # Calculate normalized load (0.0 to 1.0)
        normalized_load = min(1.0, max(0.0, node_load / 100.0))
        
        # Use the advanced latency_ms method
        latency_ms = self.latency_ms(node_type, normalized_load, task_size_mb)
        
        # Convert from milliseconds to seconds (as expected by Node.execute_task)
        return latency_ms / 1000.0

    def __repr__(self):
        return f"<Simu5GAdapter endpoint={self.endpoint}>"


# ---------------------------------------------------------------------
# Simulator factory registry
# ---------------------------------------------------------------------
_AVAILABLE_SIMULATORS = {
    "simple": FiveGDistributedSimulator,
    "fiveg": FiveGDistributedSimulator, # Alias
    "simu5g": Simu5GAdapter,
}


def get_simulator(name: str = "simple", **kwargs):
    """
    Factory function returning an instance of the requested simulator.
      sim = get_simulator("simple")
      sim = get_simulator("simu5g", endpoint="127.0.0.1:5555")
    """
    key = name.lower()
    if key not in _AVAILABLE_SIMULATORS:
        raise ValueError(
            f"Unknown simulator '{name}'. Available: {list(_AVAILABLE_SIMULATORS.keys())}"
        )
    return _AVAILABLE_SIMULATORS[key](**kwargs)
