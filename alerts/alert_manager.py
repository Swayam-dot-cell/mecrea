# alerts/alert_manager.py
import smtplib
import requests
import logging
from email.mime.text import MIMEText
from storage.file_store import FileStore
from storage.db_store import DBStore
from processors.firewall import Firewall

class AlertManager:
    def __init__(self, config):
        self.config = config
        self.file_store = FileStore("alerts.json")
        self.db_store = DBStore("alerts.db")
        self.firewall = Firewall()

    def send_alert(self, alert: dict):
        """Master function - trigger all alert channels."""
        self._log_console(alert)
        self._save_to_storage(alert)

        if self.config.get("email", {}).get("enabled", False):
            self._send_email(alert)

        if self.config.get("webhook", {}).get("enabled", False):
            self._send_webhook(alert)

        if alert.get("severity") == "high":
            self._auto_block(alert)

    def _log_console(self, alert: dict):
        logging.warning(f"[ALERT] {alert}")
    
    def _save_to_storage(self, alert: dict):
        """Persist alerts in file + DB."""
        self.file_store.save(alert)
        self.db_store.save(alert)

    def _send_email(self, alert: dict):
        """Send alert via email (real SMTP)."""
        email_cfg = self.config["email"]
        try:
            msg = MIMEText(str(alert))
            msg["Subject"] = f"BlueTeam ALERT: {alert.get('type')}"
            msg["From"] = email_cfg["from"]
            msg["To"] = email_cfg["to"]

            with smtplib.SMTP(email_cfg["server"], email_cfg["port"]) as server:
                server.starttls()
                server.login(email_cfg["username"], email_cfg["password"])
                server.send_message(msg)
        except Exception as e:
            logging.error(f"Email send failed: {e}")

    def _send_webhook(self, alert: dict):
        """Send alert to a webhook (Discord, Slack, Teams)."""
        webhook_cfg = self.config["webhook"]
        try:
            requests.post(webhook_cfg["url"], json={"text": str(alert)})
        except Exception as e:
            logging.error(f"Webhook send failed: {e}")

    def _auto_block(self, alert: dict):
        """Automatically block source IP if flagged as critical."""
        ip = alert.get("source_ip")
        if ip:
            logging.info(f"Blocking IP: {ip}")
            self.firewall.block_ip(ip)
