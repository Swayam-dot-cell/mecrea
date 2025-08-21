# processors/firewall.py
import socket
import psutil
import subprocess
import platform
import logging

logging.basicConfig(
    filename="firewall.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class Firewall:
    def __init__(self):
        self.blocked_ips = set()
        self.blocked_ports = set()

    def block_ip(self, ip: str):
        """Block a given IP at OS level"""
        if ip not in self.blocked_ips:
            logging.warning(f"Blocking IP: {ip}")
            if platform.system() == "Windows":
                subprocess.call(f'netsh advfirewall firewall add rule name="Block {ip}" dir=in action=block remoteip={ip}', shell=True)
            else:
                subprocess.call(f"sudo iptables -A INPUT -s {ip} -j DROP", shell=True)
            self.blocked_ips.add(ip)

    def block_port(self, port: int):
        """Block a given port"""
        if port not in self.blocked_ports:
            logging.warning(f"Blocking Port: {port}")
            if platform.system() == "Windows":
                subprocess.call(f'netsh advfirewall firewall add rule name="Block Port {port}" dir=in action=block protocol=TCP localport={port}', shell=True)
            else:
                subprocess.call(f"sudo iptables -A INPUT -p tcp --dport {port} -j DROP", shell=True)
            self.blocked_ports.add(port)

    def monitor_connections(self):
        """Continuously monitor open connections and detect risks"""
        conns = psutil.net_connections(kind="inet")
        suspicious = []
        for c in conns:
            if c.raddr:  # remote address exists
                ip, port = c.raddr.ip, c.raddr.port
                # Example: suspicious condition (could be replaced with ML later)
                if port in [22, 3389, 4444] or ip.startswith("185."):
                    suspicious.append((ip, port))
                    self.block_ip(ip)
        return suspicious

    def alert(self, msg):
        logging.warning(f"[ALERT] {msg}")
        print(f"[FIREWALL ALERT] 🚨 {msg}")

if __name__ == "__main__":
    fw = Firewall()
    fw.alert("Firewall started monitoring...")
    while True:
        risks = fw.monitor_connections()
        for ip, port in risks:
            fw.alert(f"Suspicious connection detected: {ip}:{port}")
