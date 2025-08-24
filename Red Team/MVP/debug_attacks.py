#!/usr/bin/env python3
"""
Debug script to test all attack modules and identify issues
"""

import os
import sys
import importlib.util
import traceback

def load_module_from_file(file_path, module_name):
    """Load a Python module from a file path"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            return False, f"Could not create spec for {file_path}"
        
        module = importlib.util.module_from_spec(spec)
        if module is None:
            return False, f"Could not create module from spec for {file_path}"
        
        spec.loader.exec_module(module)
        return True, module
        
    except Exception as e:
        return False, f"Error loading module: {str(e)}"

def test_attack_module(file_path, module_name):
    """Test a single attack module"""
    print(f"\n{'='*60}")
    print(f"Testing {module_name}")
    print(f"File: {file_path}")
    print(f"{'='*60}")
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"FAILED: File not found: {file_path}")
        return False
    
    # Try to load the module
    success, result = load_module_from_file(file_path, module_name)
    if not success:
        print(f"FAILED: Failed to load module: {result}")
        return False
    
    module = result
    print(f"SUCCESS: Module loaded successfully: {module.__name__}")
    
    # Check for required functions
    if not hasattr(module, 'run'):
        print(f"FAILED: Module missing 'run' function")
        return False
    
    print(f"SUCCESS: Module has 'run' function")
    
    # Check function signature
    import inspect
    sig = inspect.signature(module.run)
    params = list(sig.parameters.keys())
    print(f"SUCCESS: Run function parameters: {params}")
    
    # Check for basic imports
    source_code = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except Exception as e:
        print(f"WARNING: Could not read source code: {e}")
    
    if source_code:
        if 'import ' in source_code or 'from ' in source_code:
            print(f"SUCCESS: Module has imports")
        else:
            print(f"WARNING: Module has no imports")
    
    # Try to run a simple test
    try:
        print(f"Testing module execution...")
        test_url = "http://httpbin.org"
        test_log = "debug_test.log"
        
        # Call the run function
        result = module.run(test_url, test_log)
        print(f"SUCCESS: Module executed successfully!")
        print(f"   Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Module execution failed: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main debug function"""
    print("Red Team Attack Module Debug Tool")
    print("=" * 60)
    
    # Define attack modules to test
    attack_modules = [
        ("red-team/attack/simple_test.py", "Simple Test"),
        ("red-team/attack/getdomain.py", "Domain Reconnaissance"),
        ("red-team/attack/formflooding.py", "Form Flooding"),
        ("red-team/attack/serverclog.py", "Server Clogging"),
        ("red-team/attack/passiverecon.py", "Passive Reconnaissance"),
        ("red-team/attack/honeytoken.py", "Honeytoken Deployment"),
    ]
    
    successful_tests = 0
    total_tests = len(attack_modules)
    
    for file_path, module_name in attack_modules:
        if test_attack_module(file_path, module_name):
            successful_tests += 1
    
    print(f"\n{'='*60}")
    print("DEBUG SUMMARY")
    print(f"{'='*60}")
    print(f"Successful tests: {successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        print("SUCCESS: All attack modules are working correctly!")
        print("READY: The Red Team system should work properly.")
    else:
        print("WARNING: Some attack modules have issues.")
        print("Please check the error messages above.")
    
    print(f"\nRecommendations:")
    if successful_tests < total_tests:
        print("1. Fix the failing modules before using the web interface")
        print("2. Check for missing dependencies")
        print("3. Verify Python syntax in failing modules")
    else:
        print("1. Start the web interface: python backend/app.py")
        print("2. Test with a safe target URL")
    
    print(f"\nDebug log file: debug_test.log")

if __name__ == "__main__":
    main()
