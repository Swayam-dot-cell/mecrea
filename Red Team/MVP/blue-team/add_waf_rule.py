import requests, os
API_BASE = os.environ.get("API_BASE","http://localhost:8000")
def send(rule, target="example.com"):
    r = requests.post(f"{API_BASE}/report/blue", json={
        "target_domain": target,
        "attack_type": "waf_rule_added",
        "payload": {"rule": rule},
        "severity": "low"
    })
    print(r.text)

if __name__ == "__main__":
    send("block_form_flood_ips")