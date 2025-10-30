import random
import time
import requests

class Task:
    """Represents a user task in a 5G network."""
    def __init__(self, task_id, size_mb, priority):
        self.task_id = task_id
        self.size_mb = size_mb
        self.priority = priority
        self.timestamp = time.time()

class Node:
    """Represents Edge or Cloud node with compute power & latency."""
    def __init__(self, name, base_latency_ms, cpu_capacity):
        self.name = name
        self.base_latency_ms = base_latency_ms
        self.cpu_capacity = cpu_capacity  # simulated compute units
        self.current_load = 0.0

    # orchestrator/environment.py  (replace only the execute_task method)
    def execute_task(self, task, network_sim=None, cloud_url=None):
        start = time.time()
        # Base processing time (depends on CPU & task size)
        proc_time = (task.size_mb / self.cpu_capacity) * 100.0
        if network_sim:
            net_latency = network_sim.get_latency(self.name, self.current_load)
        else:
            net_latency = self.base_latency_ms + random.uniform(0, 5)
         # ☁️ optional real cloud call
        if self.name.lower() == "cloud" and cloud_url:
            try:
                _ = requests.post(cloud_url, json={"task_id": task.task_id,
                                                  "size_mb": task.size_mb,
                                                  "priority": task.priority},
                                  timeout=3)
            except Exception as e:
                print(f"[warn] cloud call failed: {e}")
        total_latency = proc_time + net_latency
        # update load slightly
        self.current_load = min(1.0, self.current_load + 0.05)
        end = time.time()
        return total_latency + (end - start) * 1000  # convert s→ms

