# orchestrator/simulation.py
import random
import numpy as np

class NetworkSimulator:
    """
    Simulates varying 5G network latency and congestion for Edge and Cloud.
    """

    def __init__(self):
        # Typical 5G edge & cloud base latencies (ms)
        self.edge_base = 5
        self.cloud_base = 25

    def get_latency(self, node_type, load_factor):
        """
        Returns a simulated latency (ms) for the requested node type.
        load_factor ∈ [0,1]  -> more load = higher latency.
        """
        noise = np.random.normal(0, 2)       # small random fluctuation
        congestion = load_factor * 20        # each 0.1 load adds ~2 ms
        if node_type.lower() == "edge":
            return max(1, self.edge_base + congestion + noise)
        else:
            backbone = random.uniform(10, 30)  # internet/core latency
            return max(1, self.cloud_base + congestion + backbone + noise)
