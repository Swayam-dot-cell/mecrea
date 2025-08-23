from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
import sqlite3
import json
from pathlib import Path

# --- Initialize FastAPI app ---
app = FastAPI(title="Blue Team Dashboard API")

# --- Paths ---
DB_PATH = "storage/events.db"
ALERT_FILE = "storage/alerts.log"
DASHBOARD_PATH = Path("index.html")


# --- Helper functions ---

def fetch_events(limit=10):
    if not Path(DB_PATH).exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT timestamp, source, event_data FROM events ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()

    events = []
    for r in rows:
        try:
            event_json = json.loads(r[2])
        except:
            event_json = {}
        events.append({
            "timestamp": r[0],
            "source": r[1],
            "name": event_json.get("name", event_json.get("process", "Unknown Event")),
            "description": event_json.get("description", event_json.get("command", "No description provided")),
            "type": event_json.get("type", "activity"),
            "user": event_json.get("user", "")
        })
    return events

def fetch_alerts(limit=10):
    path = Path(ALERT_FILE)
    if not path.exists():
        return []
    with open(path, "r") as f:
        lines = f.readlines()[-limit:]
    alerts = []
    for line in lines:
        try:
            alert_json = json.loads(line).get("alert", {})
        except:
            alert_json = {}
        alerts.append({
            "timestamp": alert_json.get("timestamp"),
            "name": alert_json.get("name", "Unknown Alert"),
            "description": alert_json.get("description", "No description provided"),
            "severity": alert_json.get("severity", "info"),
            "source": alert_json.get("source", "")
        })
    return alerts

# --- API Endpoints ---

@app.get("/")
def dashboard():
    """Serve dashboard HTML"""
    return FileResponse(DASHBOARD_PATH)

@app.get("/status")
def get_status():
    return {"status": "running", "message": "Blue Team system is active 🚀"}

@app.get("/events")
def get_events(limit: int = 10):
    return fetch_events(limit)

@app.get("/alerts")
def get_alerts(limit: int = 10):
    return fetch_alerts(limit)
