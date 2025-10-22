import random
from orchestrator.environment import Task, Node

class RandomOrchestrator:
    """Baseline: randomly assigns tasks to Edge or Cloud."""
    def __init__(self, edge_node: Node, cloud_node: Node):
        self.edge = edge_node
        self.cloud = cloud_node

    def assign_task(self, task: Task):
        node = random.choice([self.edge, self.cloud])
        latency = node.execute_task(task)
        return node.name, latency
