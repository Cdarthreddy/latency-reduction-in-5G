# orchestrator/environment.py
from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Optional

try:
    # optional import so Week-6 still runs without the new file
    from orchestrator.sim_interface import NetworkSimulator
except Exception:  # pragma: no cover
    NetworkSimulator = None  # type: ignore


@dataclass
# orchestrator/environment.py

class Task:
    """
    Represents a computational task with an app type, size (MB), and priority.
    """
    def __init__(self, task_id, app_type, size_mb, priority):
        self.task_id = task_id
        self.app_type = app_type
        self.size_mb = size_mb
        self.priority = priority

    def __repr__(self):
        return f"Task(id={self.task_id}, app={self.app_type}, size={self.size_mb}MB, prio={self.priority})"


class Node:
    """
    Represents a compute node — edge or cloud — capable of executing tasks.
    """
    def __init__(self, node_id, node_type, capacity_mbps):
        self.node_id = node_id
        self.node_type = node_type.lower()  # "edge" or "cloud"
        self.capacity_mbps = capacity_mbps
        self.current_load = 0.0
        self.name = f"{self.node_type}_{self.node_id}"   # ensures main.py can use node.name

    def execute_task(self, task, network_sim=None):
        """
        Executes a task on this node.
        If a network simulator is provided, it adds latency accordingly.
        """
        # processing delay (seconds)
        processing_time = task.size_mb / self.capacity_mbps

        # network latency
        net_latency = 0.0
        if network_sim is not None:
            try:
                # Pass task size and current load to simulator for advanced modeling
                # Check if simulator supports enhanced signature (new simulators)
                if hasattr(network_sim, 'simulate_latency'):
                    # Try enhanced signature first (with task_size_mb and node_load)
                    try:
                        net_latency = network_sim.simulate_latency(
                            self.node_type, 
                            task.app_type, 
                            task_size_mb=task.size_mb,
                            node_load=self.current_load
                        )
                    except TypeError:
                        # Fallback to basic signature for backward compatibility
                        net_latency = network_sim.simulate_latency(self.node_type, task.app_type)
                else:
                    net_latency = 0.001  # fallback
            except Exception as e:
                # Fallback for safety
                net_latency = 0.001

        total_latency = (processing_time + net_latency) * 1000  # convert to ms
        self.current_load += task.size_mb
        return total_latency

    def reset_load(self):
        self.current_load = 0.0


