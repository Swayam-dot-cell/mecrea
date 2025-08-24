#!/usr/bin/env python3
"""
Error wrapper for attack modules to ensure they don't crash the system
"""

import sys
import traceback
import time

def safe_run_attack(attack_module, url, log_file):
    """Safely run an attack module with comprehensive error handling"""
    try:
        # Import the module dynamically
        if hasattr(attack_module, 'run'):
            print(f"[+] Executing {attack_module.__name__} attack...")
            start_time = time.time()
            
            result = attack_module.run(url, log_file)
            
            elapsed_time = time.time() - start_time
            print(f"[+] {attack_module.__name__} completed in {elapsed_time:.2f} seconds")
            
            return {
                "status": "success",
                "module": attack_module.__name__,
                "result": result,
                "elapsed_time": elapsed_time
            }
        else:
            return {
                "status": "failed",
                "module": attack_module.__name__,
                "error": "Module does not have a 'run' function",
                "elapsed_time": 0
            }
            
    except ImportError as e:
        return {
            "status": "failed",
            "module": getattr(attack_module, '__name__', 'Unknown'),
            "error": f"Import error: {str(e)}",
            "elapsed_time": 0
        }
    except Exception as e:
        error_traceback = traceback.format_exc()
        return {
            "status": "failed",
            "module": getattr(attack_module, '__name__', 'Unknown'),
            "error": f"Execution error: {str(e)}",
            "traceback": error_traceback,
            "elapsed_time": 0
        }

def test_module_import(module_name):
    """Test if a module can be imported without errors"""
    try:
        module = __import__(module_name)
        return True, module
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    print("Error wrapper module - not meant to be run directly")
