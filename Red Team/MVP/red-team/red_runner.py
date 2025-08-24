# red-team/attack/red_runner.py
import subprocess, json, sys, time
from pathlib import Path
from datetime import datetime
from log_monitor.log_monitor import append_event

SCRIPTS = [
    "red-team/attack/getdomain.py",
    "red-team/attack/passiverecon.py",
    "red-team/attack/formflooding.py",
    "red-team/attack/serverclog.py",
    "red-team/attack/honeypot.py",
]

OUT = Path("red_report.json")

def run_all(target_url):
    metas = []
    start = time.time()
    for script in SCRIPTS:
        t0 = datetime.utcnow().isoformat() + "Z"
        try:
            # run script sequentially; pass target_url as arg where needed
            subprocess.run(["python3", script, target_url], check=True, timeout=120)
            status = "success"
        except subprocess.CalledProcessError:
            status = "error"
        except Exception as e:
            status = "error"
        t1 = datetime.utcnow().isoformat() + "Z"
        meta = {"script": script.split("/")[-1], "status": status, "started": t0, "finished": t1}
        metas.append(meta)
        append_event("ATTACK_TOOL_RUN", {"tool": meta["script"], "status": status, "target": target_url})
    total_time = time.time() - start
    report = {
        "report_type": "red_team",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "target": target_url,
        "tools": metas,
        "duration_seconds": total_time
    }
    OUT.write_text(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python red_runner.py <target_url>")
        sys.exit(1)
    import os
    # ensure log_monitor package path
    run_all(sys.argv[1])
    print("red_report.json created")
