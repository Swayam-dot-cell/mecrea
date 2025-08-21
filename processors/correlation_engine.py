from collections import defaultdict
import time

class CorrelationEngine:
    def __init__(self):
        self.event_cache = defaultdict(list)

    def correlate(self, alerts: list) -> list:
        correlated = []
        now = time.time()
        for alert in alerts:
            src = alert["log"].get("source_ip", "unknown")
            self.event_cache[src].append((now, alert))

            # Example: multiple alerts from same IP in <60s
            recent_events = [e for t, e in self.event_cache[src] if now - t < 60]
            if len(recent_events) >= 3:
                correlated.append({
                    "severity": "high",
                    "message": f"Multiple suspicious events from {src}",
                    "events": recent_events
                })
        return correlated
