from orchestrator.environment import Task, Node

class RuleBasedOrchestrator:
    """
    Deterministic policy:
      • Send to Edge if task size < 5 MB  OR priority == 'high'
      • Otherwise send to Cloud
    """
    def __init__(self, edge_node: Node, cloud_node: Node):
        self.edge = edge_node
        self.cloud = cloud_node

    def assign_task(self, task: Task):
        if task.size_mb < 5 or task.priority == "high":
            node = self.edge
        else:
            node = self.cloud
        latency = node.execute_task(task)
        return node.name, latency
