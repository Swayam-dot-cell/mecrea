import requests
import time
import random
import string
import uuid

def create_honeytoken():
    """Create a unique honeytoken with realistic data."""
    first_names = ["John", "Jane", "Mike", "Sarah", "David", "Lisa", "Tom", "Emma", "Alex", "Maria"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    
    return {
        "token_id": str(uuid.uuid4()),
        "username": f"user_{random.randint(1000, 9999)}",
        "password": ''.join(random.choices(string.ascii_letters + string.digits, k=12)),
        "email": f"{random.randint(1000, 9999)}@example.com",
        "first_name": random.choice(first_names),
        "last_name": random.choice(last_names),
        "phone": f"+1{random.randint(100, 999)}{random.randint(100, 999)}{random.randint(1000, 9999)}",
        "company": f"Company_{random.randint(100, 999)}",
        "created_at": time.time()
    }

def submit_to_phishing_site(url, honeytoken):
    """Submit honeytoken to phishing site with multiple endpoints."""
    endpoints = [
        "/register", "/signup", "/create-account", "/join", "/subscribe",
        "/contact", "/feedback", "/support", "/newsletter", "/download"
    ]
    
    successful_submissions = 0
    failed_submissions = 0
    
    for endpoint in endpoints:
        try:
            target_url = f"{url.rstrip('/')}{endpoint}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Connection': 'keep-alive',
            }
            
            response = requests.post(
                target_url, 
                data=honeytoken,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201, 302]:
                print(f"[+] Successfully submitted honeytoken to {endpoint}: {response.status_code}")
                successful_submissions += 1
            else:
                print(f"[!] Failed to submit to {endpoint}: {response.status_code}")
                failed_submissions += 1
                
        except Exception as e:
            print(f"[!] Error submitting to {endpoint}: {e}")
            failed_submissions += 1
    
    return {"successful": successful_submissions, "failed": failed_submissions}

def submit_to_multiple_forms(url, honeytoken):
    """Submit honeytoken to multiple form variations."""
    form_variations = [
        # Standard registration form
        {
            "username": honeytoken["username"],
            "password": honeytoken["password"],
            "email": honeytoken["email"],
            "confirm_password": honeytoken["password"]
        },
        # Contact form
        {
            "name": f"{honeytoken['first_name']} {honeytoken['last_name']}",
            "email": honeytoken["email"],
            "phone": honeytoken["phone"],
            "company": honeytoken["company"],
            "message": f"Interested in your services. Please contact me at {honeytoken['email']}"
        },
        # Newsletter subscription
        {
            "email": honeytoken["email"],
            "first_name": honeytoken["first_name"],
            "last_name": honeytoken["last_name"],
            "subscribe": "true"
        },
        # Download form
        {
            "email": honeytoken["email"],
            "name": f"{honeytoken['first_name']} {honeytoken['last_name']}",
            "company": honeytoken["company"],
            "purpose": "research"
        }
    ]
    
    successful_submissions = 0
    failed_submissions = 0
    
    for i, form_data in enumerate(form_variations):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Connection': 'keep-alive',
            }
            
            response = requests.post(url, data=form_data, headers=headers, timeout=10)
            
            if response.status_code in [200, 201, 302]:
                print(f"[+] Form variation {i+1} submitted successfully: {response.status_code}")
                successful_submissions += 1
            else:
                print(f"[!] Form variation {i+1} failed: {response.status_code}")
                failed_submissions += 1
                
        except Exception as e:
            print(f"[!] Form variation {i+1} error: {e}")
            failed_submissions += 1
    
    return {"successful": successful_submissions, "failed": failed_submissions}

def run_honeytoken_submission(url):
    """Main function to run honeytoken submission attack."""
    print(f"[+] Starting honeytoken submission attack on: {url}")
    
    # Create multiple honeytokens
    honeytokens = [create_honeytoken() for _ in range(3)]
    
    total_successful = 0
    total_failed = 0
    
    for i, honeytoken in enumerate(honeytokens):
        print(f"\n[+] Deploying honeytoken {i+1}: {honeytoken['token_id']}")
        print(f"    Username: {honeytoken['username']}")
        print(f"    Email: {honeytoken['email']}")
        
        # Submit to multiple endpoints
        endpoint_results = submit_to_phishing_site(url, honeytoken)
        total_successful += endpoint_results["successful"]
        total_failed += endpoint_results["failed"]
        
        # Submit to multiple form variations
        form_results = submit_to_multiple_forms(url, honeytoken)
        total_successful += form_results["successful"]
        total_failed += form_results["failed"]
        
        # Small delay between tokens
        time.sleep(1)
    
    print(f"\n[+] Honeytoken attack completed!")
    print(f"[+] Total successful submissions: {total_successful}")
    print(f"[+] Total failed submissions: {total_failed}")
    print(f"[+] Honeytokens deployed: {len(honeytokens)}")
    
    return {
        "honeytokens_deployed": len(honeytokens),
        "successful_submissions": total_successful,
        "failed_submissions": total_failed,
        "honeytoken_details": honeytokens
    }

def run(url, log_file):
    """Run honeytoken submission and log the results."""
    print(f"[+] Starting honeytoken attack on: {url}")
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[HoneyToken] Starting attack on: {url}\n")
    
    try:
        result = run_honeytoken_submission(url)
        
        # Log results
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[HoneyToken] Attack completed\n")
            f.write(f"[HoneyToken] Results: {result}\n\n")
        
        print(f"[+] Honeytoken attack completed for: {url}")
        return result
        
    except Exception as e:
        error_msg = f"Honeytoken attack failed: {e}"
        print(f"[!] {error_msg}")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[HoneyToken] Error: {error_msg}\n\n")
        
        return {"error": error_msg}

if __name__ == "__main__":
    url = input("Enter phishing site URL: ").strip()
    run(url, "honeytoken_attack.log")