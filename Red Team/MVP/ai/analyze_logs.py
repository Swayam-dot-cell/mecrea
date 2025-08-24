# ai/analyze_logs.py
import os, json
from pathlib import Path
from datetime import datetime
from openai import OpenAI  # pip install openai
from dotenv import load_dotenv
from log_monitor.log_monitor import append_event

load_dotenv()
API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API")  # support variations
client = OpenAI(api_key=API_KEY) if API_KEY else None

LOGFILE = Path("all_logs.json")
OUT = Path("ai_insights.json")

def craft_prompt(logs):
    # Keep prompt concise: ask for JSON output with specific keys
    prompt = f"""
You are a cybersecurity assistant. Given the logs list below, produce a JSON object with the following fields:
- summary: short text summary (1-3 sentences)
- high_risks: list of strings
- medium_risks: list of strings
- low_risks: list of strings
- recommended_actions: list of objects {{"action": "...", "reason": "...", "priority": "High/Medium/Low"}}
- detected_vectors: list of strings
- flagged_ips: list of IP strings
- sample_events: up to 5 representative log entries
Return ONLY valid JSON.

Logs:
{json.dumps(logs)}
"""
    return prompt

def analyze_with_openai():
    if not client:
        print("OpenAI API key not provided. Skipping AI analysis")
        return None
    logs = []
    if LOGFILE.exists():
        logs = json.loads(LOGFILE.read_text())
    prompt = craft_prompt(logs)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",  # adjust if not available; fallback to gpt-3.5-turbo if needed
        messages=[{"role":"user","content":prompt}],
        temperature=0.2,
        max_tokens=1200
    )
    content = resp.choices[0].message["content"]
    try:
        # try parsing the assistant text as JSON
        data = json.loads(content)
    except Exception:
        # if assistant returned something else, wrap it
        data = {"raw": content}
    data["generated_at"] = datetime.utcnow().isoformat() + "Z"
    OUT.write_text(json.dumps(data, indent=2))
    append_event("AI_ANALYSIS", {"ai_file": str(OUT), "ai_model":"gpt-4o-mini"})
    return data

if __name__ == "__main__":
    print("running ai analyze")
    analyze_with_openai()
