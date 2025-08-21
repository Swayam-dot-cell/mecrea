# monitors/suricata_monitor.py
import json
import time
from pathlib import Path
import logging, logging.config
import subprocess, platform

logging.config.fileConfig("config/logging.conf")
logger = logging.getLogger("blue_team")

DEFAULT_EVE = r"C:\ProgramData\Suricata\log\eve.json"  # change if needed

def _block_ip_windows(ip):
    try:
        # create a rule name unique per ip
        rule_name = f"BlueTeamBlock-{ip}"
        subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule",
                        f"name={rule_name}", "dir=in", "action=block", f"remoteip={ip}"],
                       check=False)
        logger.info(f"Windows firewall: blocked {ip}")
    except Exception as e:
        logger.exception("Failed to block IP on Windows: %s", e)

def _block_ip_linux(ip):
    try:
        # example using iptables
        subprocess.run(["sudo", "iptables", "-I", "INPUT", "-s", ip, "-j", "DROP"], check=False)
        logger.info(f"iptables: blocked {ip}")
    except Exception as e:
        logger.exception("Failed to block IP on Linux: %s", e)

def auto_block_ip(ip):
    if not ip:
        return
    if platform.system().lower().startswith("win"):
        _block_ip_windows(ip)
    else:
        _block_ip_linux(ip)

def monitor_suricata(callback, eve_path=None, auto_block=False):
    path = Path(eve_path or DEFAULT_EVE)
    pos = 0
    logger.info("Suricata monitor watching %s", path)
    while True:
        if not path.exists():
            logger.debug("Suricata eve.json not found, sleeping...")
            time.sleep(1)
            continue
        with path.open("rb") as f:
            f.seek(pos)
            for _ in range(1000):
                line = f.readline()
                if not line:
                    break
                try:
                    j = json.loads(line.decode("utf-8", errors="ignore"))
                    evt_type = j.get("event_type")
                    if evt_type == "alert":
                        alert = {
                            "source": "suricata",
                            "timestamp": j.get("timestamp"),
                            "event_type": "suricata_alert",
                            "signature": j.get("alert", {}).get("signature"),
                            "category": j.get("alert", {}).get("category"),
                            "severity": j.get("alert", {}).get("severity"),
                            "src_ip": j.get("src_ip"),
                            "dst_ip": j.get("dest_ip") or j.get("dst_ip"),
                            "payload": j
                        }
                        callback(alert)
                        # optional blocking
                        if auto_block:
                            offender = alert.get("src_ip") or alert.get("dst_ip")
                            auto_block_ip(offender)
                    else:
                        # other event types (dns/http)
                        base = {
                            "source": "suricata",
                            "timestamp": j.get("timestamp"),
                            "event_type": evt_type or "suricata_event",
                            **j
                        }
                        callback(base)
                except Exception as ex:
                    logger.debug("Bad eve.json line: %s", ex)
            pos = f.tell()
        time.sleep(0.3)
