# monitors/tshark_monitor.py
import subprocess
import json
import logging
import logging.config
import time

logging.config.fileConfig("config/logging.conf")
logger = logging.getLogger("blue_team")

TSHARK_CMD_BASE = ["tshark", "-l", "-T", "json"]  # requires tshark in PATH

def _extract_from_layers(layers):
    # helper to read nested keys safely
    def _get(path, default=None):
        cur = layers
        for k in path.split("."):
            if not isinstance(cur, dict):
                return default
            cur = cur.get(k)
            if cur is None:
                return default
        return cur

    return {
        "frame_time": _get("frame.frame.time"),
        "protocols": _get("frame.frame.protocols"),
        "src_ip": _get("ip.ip.src"),
        "dst_ip": _get("ip.ip.dst"),
        "src_port": _get("tcp.tcp.srcport") or _get("udp.udp.srcport"),
        "dst_port": _get("tcp.tcp.dstport") or _get("udp.udp.dstport"),
        "dns_qry": _get("dns.dns.qry.name"),
        "http_host": _get("http.http.host"),
        "http_uri": _get("http.http.request.full_uri") or _get("http.http.request.uri"),
        "tls_sni": _get("tls.handshake.extensions_server_name") or _get("ssl.handshake.extensions_server_name")
    }

def monitor_tshark(callback, iface=None, capture_filter=None):
    """
    Blocking: runs tshark and parses JSON output. Calls callback(normalized_event_dict).
    """
    cmd = list(TSHARK_CMD_BASE)
    if iface:
        cmd += ["-i", str(iface)]
    if capture_filter:
        cmd += ["-f", capture_filter]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        logger.error("tshark not found in PATH. Install Wireshark/tshark.")
        return
    except Exception as ex:
        logger.exception("Failed to start tshark: %s", ex)
        return

    buffer = b""
    while True:
        try:
            chunk = proc.stdout.readline()
            if not chunk:
                time.sleep(0.1)
                continue
            buffer += chunk
            # tshark may output many JSON values; attempt to decode when buffer ends with ]
            if buffer.strip().endswith(b"]"):
                try:
                    arr = json.loads(buffer.decode("utf-8", errors="ignore"))
                except Exception:
                    buffer = b""
                    continue
                for item in arr:
                    layers = item.get("_source", {}).get("layers", {})
                    data = _extract_from_layers(layers)
                    # Choose event_type
                    event_type = "network_flow"
                    if data["dns_qry"]:
                        event_type = "dns_query"
                    elif data["http_host"] or data["http_uri"]:
                        event_type = "http_request"
                    elif data["tls_sni"]:
                        event_type = "tls_sni"
                    evt = {
                        "source": "tshark",
                        "timestamp": data.get("frame_time"),
                        "event_type": event_type,
                        "src_ip": data.get("src_ip"),
                        "dst_ip": data.get("dst_ip"),
                        "src_port": data.get("src_port"),
                        "dst_port": data.get("dst_port"),
                        "dns_qry": data.get("dns_qry"),
                        "http_host": data.get("http_host"),
                        "http_uri": data.get("http_uri"),
                        "tls_sni": data.get("tls_sni"),
                        "protocols": data.get("protocols")
                    }
                    callback(evt)
                buffer = b""
        except Exception as ex:
            logger.exception("tshark read error: %s", ex)
            time.sleep(1)
