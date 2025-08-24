#!/usr/bin/env python3
"""
Test script to verify all red team attack modules work correctly.
Run this script to test the attacks without the web interface.
"""

import sys
import os

# Add the red-team directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'red-team'))

def test_attack_module(module_name, module_path, target_url):
    """Test a single attack module."""
    print(f"\n{'='*60}")
    print(f"Testing {module_name}")
    print(f"{'='*60}")
    
    try:
        # Import the module
        spec = __import__(module_name)
        
        # Test the run function
        if hasattr(spec, 'run'):
            print(f"[+] Testing {module_name}.run() function...")
            result = spec.run(target_url, "test_attack.log")
            print(f"[+] {module_name} completed successfully!")
            print(f"[+] Result: {result}")
            return True
        else:
            print(f"[!] {module_name} does not have a 'run' function")
            return False
            
    except ImportError as e:
        print(f"[!] Failed to import {module_name}: {e}")
        return False
    except Exception as e:
        print(f"[!] Error testing {module_name}: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Red Team Attack Module Test Suite")
    print("=" * 60)
    
    # Test target URL
    target_url = "http://httpbin.org"  # Safe test target
    
    print(f"Target URL: {target_url}")
    print("Note: Using httpbin.org as a safe test target")
    
    # List of attack modules to test
    attack_modules = [
        ("getdomain", "red-team/attack/getdomain.py"),
        ("formflooding", "red-team/attack/formflooding.py"),
        ("serverclog", "red-team/attack/serverclog.py"),
        ("passiverecon", "red-team/attack/passiverecon.py"),
        ("honeytoken", "red-team/attack/honeytoken.py"),
    ]
    
    successful_tests = 0
    total_tests = len(attack_modules)
    
    for module_name, module_path in attack_modules:
        if test_attack_module(module_name, module_path, target_url):
            successful_tests += 1
    
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Successful tests: {successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        print("🎉 All attack modules are working correctly!")
        print("✅ The Red Team system is ready for use.")
    else:
        print("⚠️  Some attack modules have issues.")
        print("Please check the error messages above.")
    
    print(f"\nTest log file: test_attack.log")

if __name__ == "__main__":
    main()
