# blue-team/blue_runner.py
import subprocess, json, time, sys
from pathlib import Path
from datetime import datetime
from log_monitor.log_monitor import append_event

SCRIPTS = [
    "blue-team/add_waf_rule.py",
    "blue-team/block_ip.py",
    "blue-team/rate_limit.py",
]

OUT = Path("blue_report.json")

def run_all():
    metas = []
    start = time.time()
    for script in SCRIPTS:
        t0 = datetime.utcnow().isoformat() + "Z"
        try:
            subprocess.run(["python3", script], check=True, timeout=120)
            status = "success"
        except Exception as e:
            status = "error"
        t1 = datetime.utcnow().isoformat() + "Z"
        meta = {"script": script.split("/")[-1], "status": status, "started": t0, "finished": t1}
        metas.append(meta)
        append_event("DEFENSE_TOOL_RUN", {"tool": meta["script"], "status": status})
    total = time.time() - start
    report = {
        "report_type": "blue_team",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "actions": metas,
        "duration_seconds": total
    }
    OUT.write_text(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    run_all()
    print("blue_report.json created")
