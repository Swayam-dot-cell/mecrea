import json
import os

class ThreatDetector:
    def __init__(self, rules_file="intel/rules.json", dynamic_file="intel/rules_dynamic.json"):
        self.rules_file = rules_file
        self.dynamic_file = dynamic_file
        self.load_rules()

    def load_rules(self):
        self.rules = []
        for f in [self.rules_file, self.dynamic_file]:
            if os.path.exists(f):
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(f)
                    self.rules.extend(data)

    def detect(self, log):
        detected = []
        for rule in self.rules:
            keyword = rule.get("keyword", "").lower()
            if keyword and keyword in str(log).lower():
                detected.append(rule.get("description", "Matched rule"))
                # Optional: add to dynamic rules if repeated
                self._update_dynamic_rules(keyword, rule.get("severity", "low"))
        return detected

    def _update_dynamic_rules(self, keyword, severity):
        dyn_rules = []
        if os.path.exists(self.dynamic_file):
            with open(self.dynamic_file, "r", encoding="utf-8") as f:
                dyn_rules = json.load(f)

        if not any(r.get("keyword") == keyword for r in dyn_rules):
            dyn_rules.append({
                "keyword": keyword,
                "severity": severity,
                "description": f"Auto-added: {keyword}"
            })
            with open(self.dynamic_file, "w", encoding="utf-8") as f:
                json.dump(dyn_rules, f, indent=4)
