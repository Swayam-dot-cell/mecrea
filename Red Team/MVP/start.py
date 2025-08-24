#!/usr/bin/env python3
"""
Startup script for Quantumlock Red Team Dashboard
"""

import os
import sys
import subprocess
import time

def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")
    
    required_packages = [
        'flask', 'requests', 'beautifulsoup4', 'dnspython', 'python-whois'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"SUCCESS: {package}")
        except ImportError:
            print(f"FAILED: {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nWARNING: Missing packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r backend/requirements.txt")
        return False
    
    print("SUCCESS: All dependencies are installed!")
    return True

def start_dashboard():
    """Start the Red Team dashboard."""
    print("\nStarting Quantumlock Red Team Dashboard...")
    
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    os.chdir(backend_dir)
    
    # Start the Flask application
    try:
        print("Dashboard will be available at: http://localhost:5000")
        print("Press Ctrl+C to stop the dashboard")
        print("\n" + "="*60)
        
        subprocess.run([sys.executable, "app.py"])
        
    except KeyboardInterrupt:
        print("\n\nDashboard stopped by user")
    except Exception as e:
        print(f"\nERROR: Error starting dashboard: {e}")

def main():
    """Main function."""
    print("Quantumlock - Red Team Attack Dashboard")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\nERROR: Cannot start dashboard due to missing dependencies.")
        sys.exit(1)
    
    # Start dashboard
    start_dashboard()

if __name__ == "__main__":
    main()
