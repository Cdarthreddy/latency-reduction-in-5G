# orchestrator/random_orchestrator.py
from __future__ import annotations
import random
from orchestrator.environment import Node, Task

class RandomOrchestrator:
    """Randomly assigns each task to edge or cloud."""

    def __init__(self, edge: Node, cloud: Node):
        self.edge = edge
        self.cloud = cloud

    def assign_task(self, task: Task):
        node = self.edge if random.choice([True, False]) else self.cloud
        latency = node.execute_task(task)
        return node.name, latency
