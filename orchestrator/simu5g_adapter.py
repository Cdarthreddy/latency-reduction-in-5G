# orchestrator/simu5g_adapter.py
"""
Pretends to query an external 5G network simulator (Simu5G/NS-3).
"""

import random, time
from orchestrator.sim_interface import NetworkSimulator

class Simu5GAdapter(NetworkSimulator):
    def __init__(self, endpoint: str | None = None, simulate_delay: bool = True):
        self.endpoint = endpoint or "localhost:5555"
        self.simulate_delay = simulate_delay

    def latency_ms(self, node_type: str, load: float, task_size_mb: float) -> float:
        base_edge = 4.5
        base_cloud = 22.0
        load_penalty = 25.0 * load
        noise = random.uniform(-1.5, 1.5)
        size_effect = 0.5 * (task_size_mb ** 0.5)

        if "edge" in node_type.lower():
            latency = base_edge + load_penalty + noise + size_effect
        else:
            backbone = random.uniform(10, 30)
            latency = base_cloud + backbone + load_penalty + noise + size_effect

        if self.simulate_delay:
            time.sleep(0.0005)
        return max(1.0, latency)
