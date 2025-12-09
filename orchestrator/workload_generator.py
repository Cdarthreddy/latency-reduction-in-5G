# orchestrator/workload_generator.py
"""
Enhanced synthetic workload generator for 5G-era tasks.
Consolidated version with Poisson inter-arrival times and flexible configuration.
"""
from __future__ import annotations
import csv
import random
import math
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Import safe print utility
try:
    from utils.console import safe_print
except ImportError:
    # Fallback if utils not available
    def safe_print(msg: str, fallback: str | None = None) -> None:
        try:
            print(msg)
        except UnicodeEncodeError:
            if fallback:
                print(fallback)
            else:
                print(msg.encode('ascii', 'replace').decode('ascii'))


class WorkloadGenerator:
    """
    Enhanced synthetic workload generator for 5G-era tasks.
    
    Produces realistic 5G-era workloads:
    - app types: IoT, ARVR, VANET
    - variable size distributions
    - Poisson-like inter-arrival times (optional)
    - Configurable priority distributions
    """

    def __init__(
        self,
        num_tasks: int = 300,
        base_time: datetime | None = None,
        poisson_lambda: float | None = None,
        random_seed: int | None = None,
        out_dir: str = "data",
        include_timestamps: bool = True,
    ):
        """
        Initialize workload generator.
        
        Args:
            num_tasks: Number of tasks to generate
            base_time: Base timestamp for task generation (default: now)
            poisson_lambda: Lambda parameter for Poisson inter-arrival times (None = no timestamps)
            random_seed: Random seed for reproducibility
            out_dir: Output directory for generated files
            include_timestamps: Whether to include timestamps in output
        """
        self.num_tasks = num_tasks
        self.poisson_lambda = poisson_lambda
        self.random_seed = random_seed
        self.base_time = base_time or datetime.now()
        self.out_dir = out_dir
        self.include_timestamps = include_timestamps and (poisson_lambda is not None)
        self.output_file = os.path.join(out_dir, "workloads.csv")

        if random_seed is not None:
            random.seed(random_seed)

        # Define app profiles (size ranges in MB)
        self.app_profiles = {
            "IoT": {
                "size_range": (0.5, 3.0),
                "priority_weights": {"low": 0.6, "medium": 0.3, "high": 0.1}
            },
            "ARVR": {
                "size_range": (5.0, 12.0),
                "priority_weights": {"low": 0.2, "medium": 0.5, "high": 0.3}
            },
            "VANET": {
                "size_range": (2.0, 8.0),
                "priority_weights": {"low": 0.3, "medium": 0.5, "high": 0.2}
            },
        }

    def _next_arrival_delta(self) -> float:
        """Generate next inter-arrival interval (seconds) using exponential distribution."""
        if self.poisson_lambda is None:
            return 0.0
        return random.expovariate(self.poisson_lambda)

    def _choose_priority(self, app_type: str) -> str:
        """Choose priority based on app type weights."""
        weights = self.app_profiles[app_type]["priority_weights"]
        return random.choices(list(weights.keys()), list(weights.values()))[0]

    def _generate_task(self, task_id: int, current_time: datetime | None = None) -> tuple:
        """Create one realistic task event."""
        app_type = random.choice(list(self.app_profiles.keys()))
        size_range = self.app_profiles[app_type]["size_range"]
        size = random.uniform(*size_range)
        priority = self._choose_priority(app_type)
        
        if self.include_timestamps and current_time is not None:
            timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
            return (task_id, timestamp, app_type, round(size, 3), priority)
        else:
            return (task_id, app_type, round(size, 3), priority)

    def generate(self) -> str:
        """
        Generate workloads.csv with tasks.
        
        Returns:
            Path to generated file
        """
        os.makedirs(self.out_dir, exist_ok=True)
        current_time = self.base_time
        tasks = []

        with open(self.output_file, "w", newline="") as f:
            writer = csv.writer(f)
            
            # Write header based on whether timestamps are included
            if self.include_timestamps:
                writer.writerow(["task_id", "timestamp", "app_type", "size_mb", "priority"])
            else:
                writer.writerow(["task_id", "app_type", "size_mb", "priority"])
            
            for i in range(self.num_tasks):
                if self.include_timestamps:
                    delta = self._next_arrival_delta()
                    current_time += timedelta(seconds=delta)
                    task = self._generate_task(i, current_time)
                else:
                    task = self._generate_task(i)
                
                writer.writerow(task)
                tasks.append(task)

        safe_print(
            f"[OK] Generated {len(tasks)} tasks -> {self.output_file}",
            fallback=f"[OK] Generated {len(tasks)} tasks -> {self.output_file}"
        )
        if tasks:
            print(f"Example: {tasks[0]}")
        return self.output_file
