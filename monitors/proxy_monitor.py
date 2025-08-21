# monitors/mitm_addon.py
from mitmproxy import http
import json, logging, logging.config
logging.config.fileConfig("config/logging.conf")
logger = logging.getLogger("blue_team")

def request(flow: http.HTTPFlow):
    try:
        evt = {
            "source": "mitmproxy",
            "timestamp": flow.request.timestamp_start,
            "event_type": "http_request",
            "client_ip": flow.client_conn.address[0] if flow.client_conn else None,
            "server_ip": flow.server_conn and getattr(flow.server_conn, "address", [None])[0],
            "method": flow.request.method,
            "host": flow.request.host,
            "path": flow.request.path,
            "headers": dict(flow.request.headers),
            "body": flow.request.get_text()[:2000]  # limit length
        }
        # Write to file for main.py to pick up or directly POST to a local socket
        with open("logs/mitm_requests.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.exception("mitm request handler failed: %s", e)

def response(flow: http.HTTPFlow):
    try:
        evt = {
            "source": "mitmproxy",
            "timestamp": flow.response.timestamp_start,
            "event_type": "http_response",
            "host": flow.request.host,
            "status_code": flow.response.status_code,
            "headers": dict(flow.response.headers),
            "body_snippet": flow.response.get_text()[:2000]
        }
        with open("logs/mitm_responses.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.exception("mitm response handler failed: %s", e)
