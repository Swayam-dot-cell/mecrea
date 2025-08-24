#!/usr/bin/env python3
"""
Simple test script to verify basic attack functionality
"""

import os
import sys

def test_basic_imports():
    """Test if basic modules can be imported"""
    print("Testing basic imports...")
    
    try:
        import requests
        print("SUCCESS: requests module imported successfully")
    except ImportError as e:
        print(f"FAILED: requests module failed: {e}")
        return False
    
    try:
        import socket
        print("SUCCESS: socket module imported successfully")
    except ImportError as e:
        print(f"FAILED: socket module failed: {e}")
        return False
    
    return True

def test_attack_module_basic(module_path, module_name):
    """Test basic attack module functionality"""
    print(f"\nTesting {module_name}...")
    
    if not os.path.exists(module_path):
        print(f"FAILED: Module file not found: {module_path}")
        return False
    
    try:
        # Read the file to check for basic syntax
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if it has the required run function
        if 'def run(' in content:
            print(f"SUCCESS: {module_name} has run function")
        else:
            print(f"FAILED: {module_name} missing run function")
            return False
        
        # Check for basic imports
        if 'import ' in content or 'from ' in content:
            print(f"SUCCESS: {module_name} has imports")
        else:
            print(f"WARNING: {module_name} has no imports")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Error reading {module_name}: {e}")
        return False

def main():
    """Main test function"""
    print("Simple Attack Module Test")
    print("=" * 40)
    
    # Test basic imports
    if not test_basic_imports():
        print("\nFAILED: Basic imports failed. Please install required packages.")
        return
    
    # Test attack modules
    attack_modules = [
        ("red-team/attack/getdomain.py", "Domain Reconnaissance"),
        ("red-team/attack/formflooding.py", "Form Flooding"),
        ("red-team/attack/serverclog.py", "Server Clogging"),
        ("red-team/attack/passiverecon.py", "Passive Reconnaissance"),
        ("red-team/attack/honeytoken.py", "Honeytoken Deployment"),
    ]
    
    successful_tests = 0
    total_tests = len(attack_modules)
    
    for module_path, module_name in attack_modules:
        if test_attack_module_basic(module_path, module_name):
            successful_tests += 1
    
    print(f"\n{'='*40}")
    print("TEST SUMMARY")
    print(f"{'='*40}")
    print(f"Successful tests: {successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        print("SUCCESS: All attack modules pass basic validation!")
        print("READY: Ready to test with web interface.")
    else:
        print("WARNING: Some modules have issues.")
        print("Please check the error messages above.")
    
    print(f"\nNext steps:")
    print("1. Start the web interface: python backend/app.py")
    print("2. Open http://localhost:5000 in your browser")
    print("3. Enter a test URL and click 'Initiate Red Team Attacks'")

if __name__ == "__main__":
    main()
