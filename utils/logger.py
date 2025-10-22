import csv
from pathlib import Path

class Logger:
    def __init__(self, filename="data/sim_results.csv"):
        Path("data").mkdir(exist_ok=True)
        self.file = open(filename, "w", newline="")
        self.writer = csv.writer(self.file)
        self.writer.writerow(["task_id", "node", "latency_ms"])

    def log(self, task_id, node, latency):
        self.writer.writerow([task_id, node, round(latency, 2)])

    def close(self):
        self.file.close()
