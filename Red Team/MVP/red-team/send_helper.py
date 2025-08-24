import requests
import os
API_BASE = os.environ.get("API_BASE", "http://localhost:8000")

def send_report(team, data):
    url = f"{API_BASE}/report/{team}"
    r = requests.post(url, json=data, timeout=10)
    try:
        return r.json()
    except:
        return {"status": r.status_code, "text": r.text}