# orchestrator/workload_generator.py
import csv
import random
from pathlib import Path

class WorkloadGenerator:
    """
    Generates synthetic 5G tasks for IoT, AR/VR, and VANET applications.
    """

    def __init__(self, num_tasks=300):
        self.num_tasks = num_tasks
        self.app_profiles = {
            "IoT":  {"size_range": (0.1, 1),  "priority": "low"},
            "ARVR": {"size_range": (5, 15),  "priority": "high"},
            "VANET":{"size_range": (2, 8),   "priority": "medium"},
        }

    def generate(self):
        Path("data").mkdir(exist_ok=True)
        with open("data/workloads.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["task_id","app_type","size_mb","priority"])
            for i in range(self.num_tasks):
                app = random.choice(list(self.app_profiles.keys()))
                cfg = self.app_profiles[app]
                size = round(random.uniform(*cfg["size_range"]), 2)
                priority = cfg["priority"]
                writer.writerow([i, app, size, priority])
        print(f"✅ Generated {self.num_tasks} synthetic tasks → data/workloads.csv")
