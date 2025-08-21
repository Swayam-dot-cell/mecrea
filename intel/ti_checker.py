import logging
import json
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='[TI_CHECKER] %(message)s')

# Load custom rules
RULES_FILE = os.path.join(os.path.dirname(__file__), "rules.json")

def load_rules():
    try:
        with open(RULES_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load rules.json: {e}")
        return {}

def check_iocs(event):
    """
    Check event against known indicators of compromise (IOCs).
    """
    rules = load_rules()
    alerts = []

    for key, values in rules.items():
        if key in event and str(event[key]) in values:
            alerts.append(f"IOC Match: {key} -> {event[key]}")

    return alerts
