#!/usr/bin/env python3
"""
Simple test attack module to verify the system is working
"""

import time
import random

def run(url, log_file):
    """Simple test attack that always succeeds"""
    print(f"[+] Starting simple test attack on: {url}")
    
    # Simulate some work
    time.sleep(1)
    
    # Generate some fake results
    results = {
        "target": url,
        "attack_type": "simple_test",
        "timestamp": time.time(),
        "status": "success",
        "data_collected": {
            "sample_data": f"test_data_{random.randint(1000, 9999)}",
            "random_value": random.random()
        }
    }
    
    # Log to file
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[SimpleTest] Attack completed on: {url}\n")
            f.write(f"[SimpleTest] Results: {results}\n\n")
    except Exception as e:
        print(f"[!] Error writing to log: {e}")
    
    print(f"[+] Simple test attack completed successfully for: {url}")
    return results

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "http://example.com"
    log_file = sys.argv[2] if len(sys.argv) > 2 else "simple_test.log"
    run(url, log_file)
