import socket
import requests
import whois
import json
from urllib.parse import urlparse
import dns.resolver
from datetime import datetime

def extract_domain_from_url(url):
    """Extract domain from URL, removing 'www.' prefix if present."""
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception as e:
        print(f"[!] Failed to parse URL: {e}")
        return None

def resolve_domain_to_ip(domain):
    """Resolve domain to its IP address."""
    try:
        ip = socket.gethostbyname(domain)
        print(f"[+] Resolved {domain} to IP: {ip}")
        return ip
    except socket.gaierror:
        print(f"[!] Failed to resolve domain: {domain}")
        return None

def get_geo_info_fallback(ip):
    """Fallback geo-lookup using ipwho.is."""
    try:
        url = f"https://ipwho.is/{ip}"
        response = requests.get(url, timeout=5)
        data = response.json()
        if not data.get("success", False):
            print(f"[!] Fallback geo lookup failed: {data.get('message', 'Unknown error')}")
            return {}
        return {
            "district": data.get("region"),  # closest approximation
            "offset": data.get("timezone", {}).get("offset"),
            "currency": data.get("currency", {}).get("code")
        }
    except Exception as e:
        print(f"[!] Fallback geo info error: {e}")
        return {}

def get_geo_info_free(ip):
    """Retrieve geo-location information using ip-api.com."""
    try:
        url = f"http://ip-api.com/json/{ip}?fields=66846719"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data['status'] != 'success':
            print(f"[!] Geo lookup failed: {data.get('message', 'Unknown error')}")
            return None
        fallback_fields = get_geo_info_fallback(ip)
        data.update(fallback_fields)
        print(f"\n[+] Geo Info for {ip}:")
        for key, value in data.items():
            print(f"    {key}: {value}")
        return data
    except Exception as e:
        print(f"[!] Failed to retrieve geo info: {e}")
        return None

def get_whois_data(domain):
    """Retrieve WHOIS data for the domain."""
    try:
        whois_data = whois.whois(domain)
        ownership = {
            "registrar": whois_data.registrar,
            "creation_date": str(whois_data.creation_date),
            "expiration_date": str(whois_data.expiration_date),
            "name_servers": whois_data.name_servers,
        }
        return ownership
    except Exception as e:
        print(f"[!] Failed to fetch WHOIS data: {e}")
        return {"error": f"Failed to fetch WHOIS data: {e}"}

def get_dns_data(domain):
    """Retrieve DNS records (A, MX, NS) for the domain."""
    dns_data = {}
    try:
        # A record
        try:
            a_record = socket.gethostbyname(domain)
        except Exception:
            a_record = "0.0.0.0"
        dns_data["A"] = a_record
        # MX records
        try:
            mx_records = socket.getaddrinfo(domain, 25, socket.AF_INET, socket.SOCK_STREAM)
            dns_data["MX"] = [record[4][0] for record in mx_records]
        except Exception:
            dns_data["MX"] = []
        # NS records
        try:
            ns_records = socket.getaddrinfo(domain, 53, socket.AF_INET, socket.SOCK_DGRAM)
            dns_data["NS"] = [record[4][0] for record in ns_records]
        except Exception:
            dns_data["NS"] = []
    except Exception as e:
        print(f"[!] Failed to fetch DNS data: {e}")
        dns_data = {"error": f"Failed to fetch DNS data: {e}"}
    return dns_data

def get_domain_info(url):
    """Retrieve comprehensive domain information (WHOIS, DNS, Geo-location)."""
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    domain = extract_domain_from_url(url)
    if not domain:
        return {"error": "Could not extract domain from URL."}
    ip = resolve_domain_to_ip(domain)
    if not ip:
        return {"error": "Could not resolve domain to IP."}
    geo_info = get_geo_info_free(ip)
    whois_info = get_whois_data(domain)
    dns_info = get_dns_data(domain)
    return {
        "domain": domain,
        "ip": ip,
        "geo_info": geo_info,
        "ownership": whois_info,
        "dns": dns_info,
    }

def run(url, log_file):
    """Run domain info gathering and log the results to the specified log file."""
    print(f"[+] Starting domain reconnaissance on: {url}")
    result = get_domain_info(url)
    
    # Log results to file
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[GetDomain] Target: {url}\n")
        f.write(f"[GetDomain] Result:\n")
        f.write(json.dumps(result, indent=2, default=str))
        f.write("\n\n")
    
    # Print results to console
    print(f"[+] Domain reconnaissance completed for: {url}")
    print(f"[+] IP Address: {result.get('ip', 'N/A')}")
    print(f"[+] Domain: {result.get('domain', 'N/A')}")
    
    return result

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else input("Enter URL: ")
    result = get_domain_info(url)
    with open("domain_info_output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    print("\n[+] Results saved to 'domain_info_output.json'.")

    from send_helper import send_report
    report = {
        "target_domain": result.get("domain", url),
        "attack_type": "getdomain",
        "payload": {
            "ip": result.get("ip"),
            "geo_info": result.get("geo_info"),
            "ownership": result.get("ownership"),
            "dns": result.get("dns"),
            "notes": "Automated domain info collection"
        },
        "severity": "info"
    }
    print(send_report("red", report))