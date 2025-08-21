import numpy as np
from sklearn.ensemble import IsolationForest

class MLDetector:
    def __init__(self):
        # Train baseline model
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.trained = False

    def train(self, logs: list):
        if not logs:
            return
        features = self._extract_features(logs)
        self.model.fit(features)
        self.trained = True

    def detect(self, log: dict) -> list:
        if not self.trained:
            return []
        features = self._extract_features([log])
        result = self.model.predict(features)
        if result[0] == -1:  # anomaly
            return [{
                "severity": "high",
                "message": "Anomalous behavior detected (ML)",
                "log": log
            }]
        return []

    def _extract_features(self, logs: list):
        # Example feature extraction (numeric encoding)
        features = []
        for log in logs:
            f = [
                len(str(log.get("process_name", ""))),
                len(str(log.get("command_line", ""))),
                int(log.get("bytes_sent", 0)),
                int(log.get("bytes_received", 0))
            ]
            features.append(f)
        return np.array(features)
