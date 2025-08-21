import json

class LogParser:
    def parse(self, raw_log: str) -> dict:
        try:
            log = json.loads(raw_log)
            # Normalize keys (lowercase, consistent)
            return {k.lower(): v for k, v in log.items()}
        except json.JSONDecodeError:
            return {"raw": raw_log}
