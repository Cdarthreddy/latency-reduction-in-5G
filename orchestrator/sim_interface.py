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

    def simulate_latency(self, node_type: str, app_type: str) -> float:
        """Simulate latency for a given node and app type."""
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
class SimpleSimulator(NetworkSimulator):
    """
    Default pluggable simulator that approximates 5G network effects.

    • Edge: small base latency, increases slightly with load.
    • Cloud: includes backbone hop and congestion noise.
    """

    def __init__(
        self,
        base_edge_ms: float = 5.0,
        base_cloud_ms: float = 25.0,
        load_factor_ms: float = 20.0,
        backbone_min_ms: float = 10.0,
        backbone_max_ms: float = 30.0,
        noise_std_ms: float = 2.0,
    ):
        self.base_edge_ms = base_edge_ms
        self.base_cloud_ms = base_cloud_ms
        self.load_factor_ms = load_factor_ms
        self.backbone_min_ms = backbone_min_ms
        self.backbone_max_ms = backbone_max_ms
        self.noise_std_ms = noise_std_ms

    # --- helpers -----------------------------------------------------
    def _gaussian_noise(self) -> float:
        # Box-Muller transform
        u1 = max(1e-12, random.random())
        u2 = max(1e-12, random.random())
        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return z0 * self.noise_std_ms

    # --- core --------------------------------------------------------
    def latency_ms(self, node_type: str, load: float, task_size_mb: float) -> float:
        t = node_type.lower()
        load = max(0.0, min(1.0, load))
        noise = self._gaussian_noise()

        size_jitter = 0.6 * math.log(max(1e-6, task_size_mb) + 1.0)

        if "edge" in t:
            return max(
                1.0,
                self.base_edge_ms + (load * self.load_factor_ms) + size_jitter + noise,
            )

        backbone = random.uniform(self.backbone_min_ms, self.backbone_max_ms)
        return max(
            1.0,
            self.base_cloud_ms + (load * self.load_factor_ms) + backbone + size_jitter + noise,
        )


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

    def __repr__(self):
        return f"<Simu5GAdapter endpoint={self.endpoint}>"


# ---------------------------------------------------------------------
# Simulator factory registry
# ---------------------------------------------------------------------
_AVAILABLE_SIMULATORS = {
    "simple": SimpleSimulator,
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
