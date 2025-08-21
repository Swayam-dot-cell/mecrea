# main.py (updated for detector + correlation)
import asyncio
import logging
import sqlite3
import json
import os
from datetime import datetime, date
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.table import Table
import signal
import yaml
import time

# --- imports: monitors + processors + alerts ---
from monitors.sysmon_monitor import monitor_sysmon
from monitors.tshark_monitor import monitor_tshark
from monitors.suricata_monitor import monitor_suricata

from processors.threat_detector import ThreatDetector
from processors.correlation_engine import CorrelationEngine  
from alerts.alert_manager import AlertManager

# -------------------------
# CONFIG
# -------------------------
DEFAULT_CONFIG = {
    "db_file": "blue_team_events.db",
    "json_dir": "logs",
    "json_rotate_daily": True,
    "batch_size": 50,
    "flush_interval": 3,
    "recent_in_memory": 25,
    "monitors": {
        "sysmon": True,
        "tshark": True,
        "suricata": True
    },
    "alerts": {}
}

CFG_PATH = Path("config/settings.yml")
if CFG_PATH.exists():
    try:
        with open(CFG_PATH, "r", encoding="utf-8") as f:
            file_cfg = yaml.safe_load(f) or {}
        cfg = {**DEFAULT_CONFIG, **file_cfg}
        if "monitors" in file_cfg:
            cfg["monitors"] = {**DEFAULT_CONFIG["monitors"], **file_cfg["monitors"]}
    except Exception:
        cfg = DEFAULT_CONFIG
else:
    cfg = DEFAULT_CONFIG

# -------------------------
# Logging
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("blue_team.log"), logging.StreamHandler()]
)
logger = logging.getLogger("blue_team")

# -------------------------
# Console UI
# -------------------------
console = Console()
recent = []
RECENT_MAX = cfg.get("recent_in_memory", 25)

# -------------------------
# DB writer
# -------------------------
DB_FILE = Path(cfg.get("db_file"))
DB_FILE.parent.mkdir(parents=True, exist_ok=True)

def init_db():
    con = sqlite3.connect(DB_FILE.as_posix(), check_same_thread=False)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            timestamp TEXT,
            event_json TEXT
        )
    """)
    con.commit()
    con.close()

# -------------------------
# JSON rotation
# -------------------------
JSON_DIR = Path(cfg.get("json_dir", "logs"))
JSON_DIR.mkdir(parents=True, exist_ok=True)

def current_json_path():
    today = date.today().isoformat()
    return JSON_DIR / f"events-{today}.jsonl"

def append_jsonl(entry: dict):
    path = current_json_path()
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# -------------------------
# Async pipeline
# -------------------------
EVENT_QUEUE = asyncio.Queue(maxsize=10000)
SHUTDOWN = False

# Initialize processors
detector = ThreatDetector(rules_file="intel/rules.json")
correlator = CorrelationEngine()
alert_mgr = AlertManager(cfg.get("alerts", {}))

# DB writer coroutine
async def db_writer(batch_size:int, flush_interval:float):
    logger.info("DB writer started")
    conn = sqlite3.connect(DB_FILE.as_posix(), check_same_thread=False)
    cur = conn.cursor()
    buffer = []
    last_flush = time.time()

    try:
        while not SHUTDOWN:
            try:
                ev = await asyncio.wait_for(EVENT_QUEUE.get(), timeout=flush_interval)
                buffer.append(ev)
            except asyncio.TimeoutError:
                pass

            if buffer and (len(buffer) >= batch_size or (time.time() - last_flush) >= flush_interval):
                try:
                    cur.executemany(
                        "INSERT INTO events (source, timestamp, event_json) VALUES (?, ?, ?)",
                        [(e["source"], e["timestamp"], json.dumps(e["event"], ensure_ascii=False)) for e in buffer]
                    )
                    conn.commit()
                    for e in buffer:
                        append_jsonl(e)
                        short = str(e["event"])
                        recent.append((e["timestamp"], e["source"], short if len(short)<200 else short[:197]+"..."))
                        if len(recent) > RECENT_MAX:
                            recent.pop(0)
                    buffer = []
                    last_flush = time.time()
                except Exception as ex:
                    logger.error(f"DB batch write error: {ex}", exc_info=True)
                    await asyncio.sleep(1)
    finally:
        if buffer:
            try:
                cur.executemany(
                    "INSERT INTO events (source, timestamp, event_json) VALUES (?, ?, ?)",
                    [(e["source"], e["timestamp"], json.dumps(e["event"], ensure_ascii=False)) for e in buffer]
                )
                conn.commit()
                for e in buffer:
                    append_jsonl(e)
            except Exception as ex:
                logger.error(f"Final DB flush failed: {ex}", exc_info=True)
        conn.close()
        logger.info("DB writer stopped")

# Event handler
def emit_event_from_thread(event: dict):
    loop = asyncio.get_event_loop()
    if SHUTDOWN:
        return
    try:
        loop.call_soon_threadsafe(asyncio.create_task, EVENT_QUEUE.put(event))
    except RuntimeError:
        pass

def process_event_sync(event: dict):
    """Run detection + correlation"""
    try:
        # ensure event["event"] is dict
        log = event["event"]
        if isinstance(log, str):
            try:
                log = json.loads(log)
            except Exception:
                log = {"raw": log}

        # run detection
        try:
            threats = detector.detect(log)
        except Exception as ex:
            logger.error(f"Detector error: {ex}", exc_info=True)

        if threats:
            for t in threats:
                alert_payload = {
                    "timestamp": event["timestamp"],
                    "source": event["source"],
                    "description": t
                }
                try:
                    alert_mgr.send_alert(alert_payload)
                except Exception as ex:
                    logger.error(f"Alert send failed: {ex}", exc_info=True)
                logger.warning(f"DETECTED: {t}")

        # correlation
        try:
            corrs = correlator.correlate([log])
            if corrs:
                for c in corrs:
                    alert_payload = {
                        "timestamp": event["timestamp"],
                        "source": event["source"],
                        "description": f"correlation: {c}"
                    }
                    try:
                        alert_mgr.send_alert(alert_payload)
                    except Exception as ex:
                        logger.error(f"Alert send failed: {ex}", exc_info=True)
                    logger.info(f"CORRELATION: {c}")
        except Exception as ex:
            logger.error(f"Correlation error: {ex}", exc_info=True)
    except Exception as ex:
        logger.error(f"process_event_sync failed: {ex}", exc_info=True)

# Monitor wrapper
def run_monitor_in_thread(monitor_fn, name):
    def callback(ev):
        standardized = {
            "source": name,
            "timestamp": ev.get("timestamp") or datetime.utcnow().isoformat(),
            "event": ev if isinstance(ev, dict) else {"raw": str(ev)}
        }
        try:
            asyncio.get_event_loop().call_soon_threadsafe(lambda: EVENT_QUEUE.put_nowait(standardized))
        except RuntimeError:
            pass

        short = str(standardized["event"])
        recent.append((standardized["timestamp"], name, short if len(short)<200 else short[:197]+"..."))
        if len(recent) > RECENT_MAX:
            recent.pop(0)

        process_event_sync(standardized)

    try:
        monitor_fn(callback)
    except Exception as ex:
        logger.error(f"{name} monitor crashed: {ex}", exc_info=True)

# Live UI
async def live_ui_updater(refresh: float = 1.0):
    from rich.live import Live
    def build_table():
        table = Table(title="🔵 Blue Team Live (recent events)", expand=True)
        table.add_column("Time", style="dim")
        table.add_column("Source", style="cyan")
        table.add_column("Event", overflow="fold")
        for ts, src, details in recent[-RECENT_MAX:]:
            table.add_row(ts, src, details)
        return table

    with Live(build_table(), refresh_per_second=1, console=console) as live:
        while not SHUTDOWN:
            live.update(build_table())
            await asyncio.sleep(refresh)

# Graceful shutdown
def _signal_handler_signals(loop):
    def _handler(sig, frame=None):
        global SHUTDOWN
        logger.info(f"Signal {sig} received, shutting down...")
        SHUTDOWN = True
        try:
            loop.call_soon_threadsafe(loop.stop)
        except Exception:
            pass
    return _handler

# Main runner
async def main():
    init_db()
    logger.info("Blue Team main starting")

    loop = asyncio.get_event_loop()
    for s in (signal.SIGINT, signal.SIGTERM):
        signal.signal(s, _signal_handler_signals(loop))

    db_task = asyncio.create_task(db_writer(cfg.get("batch_size",50), cfg.get("flush_interval",3)))
    ui_task = asyncio.create_task(live_ui_updater(1.0))

    executor = ThreadPoolExecutor(max_workers=4)
    monitor_tasks = []
    if cfg["monitors"].get("sysmon", True):
        monitor_tasks.append(loop.run_in_executor(executor, run_monitor_in_thread, monitor_sysmon, "sysmon"))
    if cfg["monitors"].get("tshark", True):
        monitor_tasks.append(loop.run_in_executor(executor, run_monitor_in_thread, monitor_tshark, "tshark"))
    if cfg["monitors"].get("suricata", True):
        monitor_tasks.append(loop.run_in_executor(executor, run_monitor_in_thread, monitor_suricata, "suricata"))

    try:
        await asyncio.gather(*(monitor_tasks + [db_task, ui_task]))
    except asyncio.CancelledError:
        logger.info("Main: cancelled")
    finally:
        logger.info("Shutting down: waiting DB writer to finish")
        await asyncio.sleep(0.5)
        if not db_task.done():
            db_task.cancel()
            try:
                await db_task
            except Exception:
                pass
        logger.info("Shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting by user request…")
    except RuntimeError as e:
        if "Event loop stopped before Future completed" in str(e):
            pass
        else:
            raise
