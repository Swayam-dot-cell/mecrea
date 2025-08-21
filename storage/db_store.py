import json
import sqlite3
from pathlib import Path
import logging, logging.config

logging.config.fileConfig("config/logging.conf")
log = logging.getLogger("blue_team")

class DBStore:
    def __init__(self, db_path="storage/events.db"):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self):
        con = sqlite3.connect(self.path.as_posix())
        con.execute("""CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            source TEXT,
            event_data TEXT
        )""")
        con.commit(); con.close()

    def save(self, event: dict):
        con = sqlite3.connect(self.path.as_posix())
        con.execute("INSERT INTO events(timestamp, source, event_data) VALUES (?,?,?)",
                    (event.get("timestamp"), event.get("source"), json.dumps(event)))
        con.commit(); con.close()
