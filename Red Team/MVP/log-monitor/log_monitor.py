# log-monitor/log_monitor.py
import json
from datetime import datetime
from pathlib import Path

LOGFILE = Path("all_logs.json")

def append_event(event_type: str, details: dict):
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "details": details
    }
    logs = []
    if LOGFILE.exists():
        try:
            logs = json.loads(LOGFILE.read_text())
        except Exception:
            logs = []
    logs.append(entry)
    LOGFILE.write_text(json.dumps(logs, indent=2))
    return entry

if __name__ == "__main__":
    # quick test
    append_event("INFO", {"msg": "Log monitor ready"})
    print("appended test entry to all_logs.json")
