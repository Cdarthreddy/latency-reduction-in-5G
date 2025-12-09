# orchestrator/generate_workloads.py
from __future__ import annotations
import csv
import random
import math
import os
from datetime import datetime, timedelta


class WorkloadGenerator:
    """
    Produces realistic 5G-era workloads:
    - app types: IoT, ARVR, VANET
    - variable size distributions
    - Poisson-like inter-arrival times
    """

    def __init__(
        self,
        num_tasks: int = 300,
        base_time: datetime | None = None,
        poisson_lambda: float = 2.5,
        random_seed: int = 42,
        out_dir: str = "data"
    ):
        self.num_tasks = num_tasks
        self.poisson_lambda = poisson_lambda
        self.random_seed = random_seed
        self.base_time = base_time or datetime.now()
        self.out_dir = out_dir
        self.output_file = os.path.join(out_dir, "workloads.csv")

        random.seed(self.random_seed)

        # Define app profiles (size ranges in MB)
        self.app_profiles = {
            "IoT":  {"size_range": (0.1, 1.0), "priority_weights": {"low": 0.6, "medium": 0.3, "high": 0.1}},
            "ARVR": {"size_range": (5.0, 20.0), "priority_weights": {"low": 0.2, "medium": 0.5, "high": 0.3}},
            "VANET": {"size_range": (2.0, 8.0), "priority_weights": {"low": 0.3, "medium": 0.5, "high": 0.2}},
        }

    # ---------------------------------------------------------------
    def _next_arrival_delta(self) -> float:
        """Generate next inter-arrival interval (seconds) using exponential distribution."""
        return random.expovariate(self.poisson_lambda)

    def _choose_priority(self, app_type: str) -> str:
        weights = self.app_profiles[app_type]["priority_weights"]
        return random.choices(list(weights.keys()), list(weights.values()))[0]

    def _generate_task(self, task_id: int, current_time: datetime) -> tuple:
        """Create one realistic task event."""
        app_type = random.choice(list(self.app_profiles.keys()))
        size_range = self.app_profiles[app_type]["size_range"]
        size = random.uniform(*size_range)
        priority = self._choose_priority(app_type)
        return (task_id, current_time.strftime("%Y-%m-%d %H:%M:%S"), app_type, round(size, 3), priority)

    # ---------------------------------------------------------------
    def generate(self) -> str:
        """Generate workloads.csv with timestamped tasks."""
        os.makedirs(self.out_dir, exist_ok=True)
        current_time = self.base_time
        tasks = []

        with open(self.output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["task_id", "timestamp", "app_type", "size_mb", "priority"])
            for i in range(self.num_tasks):
                delta = self._next_arrival_delta()
                current_time += timedelta(seconds=delta)
                task = self._generate_task(i, current_time)
                writer.writerow(task)
                tasks.append(task)

        print(f"[OK] Generated {len(tasks)} tasks -> {self.output_file}")
        print(f"Example: {tasks[0]}")
        return self.output_file


# ---------------------------------------------------------------------
if __name__ == "__main__":
    gen = WorkloadGenerator(num_tasks=300, poisson_lambda=3.0)
    gen.generate()
