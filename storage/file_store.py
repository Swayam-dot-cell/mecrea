import json
import os
from datetime import datetime

class FileStore:
    def __init__(self, base_dir="storage/data"):
        os.makedirs(base_dir, exist_ok=True)
        self.base_dir = base_dir

    def save_json(self, data, filename="events.json"):
        path = os.path.join(self.base_dir, filename)
        with open(path, "a") as f:
            f.write(json.dumps(data) + "\n")

    def save_csv(self, data, filename="events.csv"):
        import csv
        path = os.path.join(self.base_dir, filename)
        write_header = not os.path.exists(path)
        with open(path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())
            if write_header:
                writer.writeheader()
            writer.writerow(data)
