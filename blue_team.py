#!/usr/bin/env python3
"""
Professional Blue Team Security Monitor v3.0 - Fixed Version
Enterprise-grade security monitoring and threat detection system
Now includes remote website monitoring capabilities
"""

import os
import re
import time
import hashlib
import logging
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import subprocess
import json
import threading
from pathlib import Path
import socket
import psutil
import sys
import ipaddress
from typing import Dict, List, Tuple, Optional, Any
import requests
from urllib.parse import urlparse
import ssl
import urllib3

# Suppress SSL warnings for monitoring purposes
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ProfessionalBlueTeam:
    def __init__(self, config_path="config/security_config.json"):
        self.version = "3.0"
        self.startup_time = datetime.now()
        
        # Create necessary directories first
        self.create_directories()
        
        # Initialize components
        self.setup_logging()
        self.load_config(config_path)
        self.setup_database()
        self.setup_threat_intelligence()
        
        # Security state
        self.threat_counters = defaultdict(Counter)
        self.blocked_ips = set()
        self.suspicious_patterns = self.load_advanced_attack_patterns()
        self.is_admin = self.check_admin_privileges()
        
        # Website monitoring state
        self.website_status = {}
        self.monitoring_active = False
        self.monitoring_thread = None
        self._db_lock = threading.Lock()  # Add database lock for thread safety
        
        # Performance monitoring
        self.performance_stats = {
            'events_processed': 0,
            'threats_detected': 0,
            'ips_blocked': 0,
            'false_positives': 0,
            'websites_monitored': 0,
            'website_checks': 0
        }
        
        self.logger.info(f"Professional Blue Team Security Monitor v{self.version} initialized")
        
    def create_directories(self):
        """Create necessary directory structure"""
        directories = [
            "D:/quantum_lock/report",
            "D:/quantum_lock/config", 
            "D:/quantum_lock/logs",
            "D:/quantum_lock/database",
            "D:/quantum_lock/backup",
            "D:/quantum_lock/website_reports",
            "./config",  # Fallback local config directory
            "./logs",    # Fallback local logs directory
            "./reports"  # Fallback local reports directory
        ]
        
        for directory in directories:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                print(f"Warning: Could not create directory {directory}: {e}")
                # Try alternative location
                alt_dir = directory.replace("D:/quantum_lock/", "./")
                try:
                    Path(alt_dir).mkdir(parents=True, exist_ok=True)
                    print(f"Using alternative directory: {alt_dir}")
                except Exception as e2:
                    print(f"Error creating alternative directory {alt_dir}: {e2}")
    
    def check_admin_privileges(self):
        """Check if running with administrator privileges"""
        try:
            if sys.platform.startswith('win'):
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            else:
                # Unix/Linux check
                return os.geteuid() == 0
        except Exception:
            return False
        
    def setup_logging(self):
        """Setup professional logging system with multiple handlers"""
        # Clear any existing handlers to prevent duplicate logs
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        # Create custom formatter
        log_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Main logger
        self.logger = logging.getLogger('BlueTeamMonitor')
        self.logger.setLevel(logging.INFO)
        
        # Ensure logger doesn't propagate to avoid duplicate messages
        self.logger.propagate = False
        
        # Try primary log location, fallback to local
        log_paths = [
            'D:/quantum_lock/logs/security_monitor_detailed.log',
            './logs/security_monitor_detailed.log'
        ]
        
        log_file = None
        for path in log_paths:
            try:
                # Test if we can write to this location
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'a', encoding='utf-8') as test_file:
                    pass
                log_file = path
                break
            except (PermissionError, OSError) as e:
                continue
        
        if not log_file:
            log_file = './security_monitor.log'  # Last resort
        
        # File handler for detailed logs (UTF-8 encoding)
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(log_format)
            file_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")
        
        # Console handler for important events
        try:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_format)
            console_handler.setLevel(logging.INFO)
            # Set console encoding to handle Unicode
            if hasattr(console_handler.stream, 'reconfigure'):
                try:
                    console_handler.stream.reconfigure(encoding='utf-8')
                except:
                    pass
            self.logger.addHandler(console_handler)
        except Exception as e:
            print(f"Warning: Could not setup console logging: {e}")
        
        # Security events handler (separate file for security events only)
        try:
            security_log_paths = [
                'D:/quantum_lock/logs/security_events.log',
                './logs/security_events.log'
            ]
            
            security_log_file = None
            for path in security_log_paths:
                try:
                    Path(path).parent.mkdir(parents=True, exist_ok=True)
                    with open(path, 'a', encoding='utf-8') as test_file:
                        pass
                    security_log_file = path
                    break
                except:
                    continue
                    
            if security_log_file:
                security_handler = logging.FileHandler(security_log_file, encoding='utf-8')
                security_handler.setFormatter(log_format)
                security_handler.setLevel(logging.WARNING)
                self.logger.addHandler(security_handler)
        except Exception as e:
            print(f"Warning: Could not setup security event logging: {e}")
        
        # Report logger setup
        try:
            self.report_logger = logging.getLogger('UserReports')
            self.report_logger.propagate = False
            
            report_paths = [
                'D:/quantum_lock/logs/user_friendly_alerts.log',
                './logs/user_friendly_alerts.log'
            ]
            
            report_log_file = None
            for path in report_paths:
                try:
                    Path(path).parent.mkdir(parents=True, exist_ok=True)
                    with open(path, 'a', encoding='utf-8') as test_file:
                        pass
                    report_log_file = path
                    break
                except:
                    continue
                    
            if report_log_file:
                report_handler = logging.FileHandler(report_log_file, encoding='utf-8')
                report_formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%B %d, %Y at %I:%M %p')
                report_handler.setFormatter(report_formatter)
                self.report_logger.addHandler(report_handler)
        except Exception as e:
            print(f"Warning: Could not setup report logging: {e}")
        
        if not self.check_admin_privileges():
            self.logger.warning("WARNING: Not running as Administrator - IP blocking features will be limited")
        
    def load_config(self, config_path):
        """Load comprehensive configuration settings with website monitoring"""
        default_config = {
            "monitoring": {
                "scan_interval": 30,
                "deep_scan_interval": 300,
                "file_integrity_check_interval": 600,
                "network_monitor_interval": 60,
                "website_check_interval": 5
            },
            "website_monitoring": {
                "enabled": True,
                "timeout": 10,
                "max_retries": 3,
                "check_ssl": True,
                "follow_redirects": True,
                "user_agent": "Quantum Lock Security Monitor v3.0",
                "expected_status_codes": [200, 301, 302],
                "alert_on_content_change": True,
                "targets": []
            },
            "paths": {
                "monitor_directories": [
                    "C:\\Windows\\System32\\drivers\\etc" if sys.platform.startswith('win') else "/etc",
                    "C:\\Program Files" if sys.platform.startswith('win') else "/usr/bin",
                    "C:\\Users\\Public" if sys.platform.startswith('win') else "/tmp",
                    "D:\\quantum_lock" if sys.platform.startswith('win') else "./quantum_lock"
                ],
                "log_directories": [
                    "C:\\Windows\\System32\\winevt\\Logs" if sys.platform.startswith('win') else "/var/log",
                    "C:\\Windows\\Logs" if sys.platform.startswith('win') else "/var/log"
                ],
                "critical_files": [
                    "C:\\Windows\\System32\\drivers\\etc\\hosts" if sys.platform.startswith('win') else "/etc/hosts",
                    "C:\\Windows\\win.ini" if sys.platform.startswith('win') else "/etc/passwd"
                ]
            },
            "thresholds": {
                "max_requests_per_minute": 100,
                "max_failed_logins": 3,
                "max_connections_per_ip": 50,
                "suspicious_port_threshold": 5,
                "file_access_threshold": 20,
                "website_response_time_warning": 3.0,
                "website_response_time_critical": 10.0
            },
            "blocking": {
                "enable_auto_block": True,
                "block_duration": 3600,
                "permanent_block_threshold": 10,
                "whitelist_ips": ["127.0.0.1", "localhost", "::1", "10.0.0.1"]
            },
            "alerts": {
                "threat_levels": {
                    "LOW": 1,
                    "MEDIUM": 3, 
                    "HIGH": 5,
                    "CRITICAL": 10
                },
                "auto_response": {
                    "LOW": "log_only",
                    "MEDIUM": "alert",
                    "HIGH": "block_and_alert", 
                    "CRITICAL": "immediate_block"
                }
            },
            "reporting": {
                "generate_hourly_summary": True,
                "generate_daily_report": True,
                "keep_reports_days": 30,
                "include_performance_metrics": True,
                "website_report_file": self._get_report_file_path()
            }
        }
        
        config_file = Path(config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults (loaded config takes precedence)
                    self.config = self._merge_configs(default_config, loaded_config)
            except Exception as e:
                print(f"Error loading config file: {e}. Using defaults.")
                self.config = default_config
        else:
            self.config = default_config
            # Create config file
            try:
                config_file.parent.mkdir(parents=True, exist_ok=True)
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4)
            except Exception as e:
                print(f"Warning: Could not save config file: {e}")
                
    def _get_report_file_path(self) -> str:
        """Get appropriate path for report file"""
        paths = [
            "D:/quantum_lock/website_reports/reports.txt",
            "./website_reports/reports.txt",
            "./reports.txt"
        ]
        
        for path in paths:
            try:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                # Test write access
                with open(path, 'a', encoding='utf-8') as test_file:
                    pass
                return path
            except:
                continue
        return "./reports.txt"  # Fallback
                
    def _merge_configs(self, default: dict, loaded: dict) -> dict:
        """Recursively merge configuration dictionaries"""
        merged = default.copy()
        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged
        
    def setup_database(self):
        """Setup comprehensive SQLite database with website monitoring tables"""
        db_paths = [
            "D:/quantum_lock/database/security_events.db",
            "./database/security_events.db",
            "./security_events.db"
        ]
        
        db_path = None
        for path in db_paths:
            try:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                # Test database connection
                test_conn = sqlite3.connect(path, check_same_thread=False)
                test_conn.close()
                db_path = path
                break
            except Exception as e:
                continue
        
        if not db_path:
            db_path = ":memory:"  # In-memory database as last resort
            print("Warning: Using in-memory database - data will not persist")
        
        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            
            # Create tables with enhanced schema
            self.conn.executescript('''
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    threat_level TEXT NOT NULL,
                    source_ip TEXT,
                    target_ip TEXT,
                    source_port INTEGER,
                    target_port INTEGER,
                    protocol TEXT,
                    details TEXT,
                    raw_log TEXT,
                    action_taken TEXT,
                    blocked INTEGER DEFAULT 0,
                    false_positive INTEGER DEFAULT 0,
                    analyst_notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS website_monitoring (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    website_url TEXT NOT NULL,
                    status_code INTEGER,
                    response_time REAL,
                    content_hash TEXT,
                    ssl_valid INTEGER DEFAULT 0,
                    ssl_expires TEXT,
                    is_accessible INTEGER DEFAULT 1,
                    error_message TEXT,
                    content_length INTEGER,
                    redirect_url TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS file_integrity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    hash_value TEXT NOT NULL,
                    file_size INTEGER,
                    last_modified TEXT,
                    last_checked TEXT,
                    integrity_status TEXT DEFAULT 'OK',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS blocked_ips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT UNIQUE NOT NULL,
                    reason TEXT NOT NULL,
                    threat_level TEXT NOT NULL,
                    block_count INTEGER DEFAULT 1,
                    first_blocked TEXT,
                    last_blocked TEXT,
                    expires_at TEXT,
                    permanent INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS system_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_usage REAL,
                    network_connections INTEGER,
                    active_threats INTEGER,
                    websites_monitored INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON security_events(timestamp);
                CREATE INDEX IF NOT EXISTS idx_events_type ON security_events(event_type);
                CREATE INDEX IF NOT EXISTS idx_events_threat_level ON security_events(threat_level);
                CREATE INDEX IF NOT EXISTS idx_blocked_ips_ip ON blocked_ips(ip_address);
                CREATE INDEX IF NOT EXISTS idx_website_monitoring_url ON website_monitoring(website_url);
                CREATE INDEX IF NOT EXISTS idx_website_monitoring_timestamp ON website_monitoring(timestamp);
            ''')
            self.conn.commit()
            
        except Exception as e:
            print(f"Database setup error: {e}")
            # Fallback to in-memory database
            self.conn = sqlite3.connect(":memory:", check_same_thread=False)
            print("Using in-memory database as fallback")
        
    def setup_threat_intelligence(self):
        """Initialize threat intelligence and reputation systems"""
        self.threat_intel = {
            'malicious_ips': set(),
            'tor_nodes': set(),
            'known_bad_domains': set(),
            'suspicious_user_agents': set([
                'sqlmap', 'nikto', 'nessus', 'burp', 'dirbuster', 
                'gobuster', 'wfuzz', 'masscan', 'nmap', 'zap'
            ])
        }
        
        # Load threat intelligence from file if exists
        threat_intel_paths = [
            "D:/quantum_lock/config/threat_intelligence.json",
            "./config/threat_intelligence.json"
        ]
        
        for path in threat_intel_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.threat_intel['malicious_ips'].update(data.get('malicious_ips', []))
                        self.threat_intel['known_bad_domains'].update(data.get('bad_domains', []))
                    break
                except Exception as e:
                    print(f"Warning: Could not load threat intelligence from {path}: {e}")
    
    def load_advanced_attack_patterns(self):
        """Load comprehensive attack detection patterns"""
        return {
            'sql_injection': {
                'patterns': [
                    r"(\bunion\b.*\bselect\b)",
                    r"(\bor\b.*=.*)",
                    r"(\bdrop\b.*\btable\b)",
                    r"(\binsert\b.*\binto\b)",
                    r"(\bupdate\b.*\bset\b)",
                    r"(\bdelete\b.*\bfrom\b)",
                    r"(\bselect\b.*\bfrom\b)",
                    r"('.*or.*'.*=.*')",
                    r"(\-\-|\#|\/\*)",
                    r"(0x[0-9a-f]+)",
                    r"(waitfor\s+delay)",
                    r"(benchmark\s*\()",
                    r"(pg_sleep\s*\()",
                    r"(sleep\s*\(\s*\d+\s*\))"
                ],
                'severity': 'HIGH',
                'description': 'Attempt to inject malicious SQL code'
            },
            'xss': {
                'patterns': [
                    r"<script[^>]*>",
                    r"javascript:",
                    r"on\w+\s*=",
                    r"<iframe[^>]*>",
                    r"<object[^>]*>",
                    r"<embed[^>]*>",
                    r"alert\s*\(",
                    r"document\.cookie",
                    r"eval\s*\(",
                    r"String\.fromCharCode",
                    r"<svg.*onload"
                ],
                'severity': 'HIGH',
                'description': 'Cross-Site Scripting attack attempt'
            },
            'path_traversal': {
                'patterns': [
                    r"\.\./",
                    r"\.\.\\",
                    r"%2e%2e%2f",
                    r"%252e%252e%252f",
                    r"\.\.%2f",
                    r"\.\.%5c",
                    r"..%c0%af",
                    r"..%c1%9c"
                ],
                'severity': 'HIGH',
                'description': 'Directory traversal attack'
            },
            'command_injection': {
                'patterns': [
                    r";\s*(dir|type|del|copy|move)",
                    r"\|\s*(dir|type|del)",
                    r"cmd\.exe",
                    r"powershell",
                    r"net\s+user",
                    r"tasklist",
                    r"systeminfo",
                    r"whoami",
                    r"ipconfig",
                    r"netstat"
                ],
                'severity': 'CRITICAL',
                'description': 'Command injection attempt'
            },
            'brute_force': {
                'patterns': [
                    r"(failed|invalid).*login",
                    r"authentication.*fail",
                    r"access.*denied",
                    r"invalid.*credentials"
                ],
                'severity': 'MEDIUM',
                'description': 'Brute force login attempt'
            },
            'dos_attack': {
                'patterns': [
                    r"slowloris",
                    r"slowhttptest",
                    r"r-u-dead-yet",
                    r"pyloris"
                ],
                'severity': 'HIGH',
                'description': 'Denial of Service attack'
            },
            'web_shell': {
                'patterns': [
                    r"c99\.php",
                    r"r57\.php",
                    r"webshell",
                    r"eval\s*\(\s*\$_POST",
                    r"system\s*\(\s*\$_GET",
                    r"passthru\s*\(",
                    r"shell_exec\s*\("
                ],
                'severity': 'CRITICAL',
                'description': 'Web shell upload or execution attempt'
            }
        }

    def add_website_target(self, url: str, name: str = None):
        """Add a website to monitor"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        target = {
            'url': url,
            'name': name or urlparse(url).netloc,
            'added_at': datetime.now().isoformat()
        }
        
        if 'website_monitoring' not in self.config:
            self.config['website_monitoring'] = {'targets': []}
        
        if 'targets' not in self.config['website_monitoring']:
            self.config['website_monitoring']['targets'] = []
        
        # Check if URL already exists
        existing_urls = [t['url'] for t in self.config['website_monitoring']['targets']]
        if url not in existing_urls:
            self.config['website_monitoring']['targets'].append(target)
            
            # Save config
            config_paths = ["config/security_config.json", "./security_config.json"]
            for config_file in config_paths:
                try:
                    Path(config_file).parent.mkdir(parents=True, exist_ok=True)
                    with open(config_file, 'w', encoding='utf-8') as f:
                        json.dump(self.config, f, indent=4)
                    break
                except Exception as e:
                    continue
                    
            if hasattr(self, 'logger'):
                self.logger.info(f"Added website target: {target['name']} ({url})")
            else:
                print(f"Added website target: {target['name']} ({url})")
        else:
            if hasattr(self, 'logger'):
                self.logger.info(f"Website target already exists: {url}")
            else:
                print(f"Website target already exists: {url}")
        
    def start_website_monitoring(self):
        """Start continuous website monitoring in a separate thread"""
        if self.monitoring_active:
            if hasattr(self, 'logger'):
                self.logger.warning("Website monitoring is already running")
            else:
                print("Website monitoring is already running")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._website_monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        if hasattr(self, 'logger'):
            self.logger.info("Website monitoring started")
        else:
            print("Website monitoring started")
        
    def stop_website_monitoring(self):
        """Stop website monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=10)
            
        if hasattr(self, 'logger'):
            self.logger.info("Website monitoring stopped")
        else:
            print("Website monitoring stopped")
        
    def _website_monitoring_loop(self):
        """Main website monitoring loop"""
        while self.monitoring_active:
            try:
                targets = self.config.get('website_monitoring', {}).get('targets', [])
                if not targets:
                    if hasattr(self, 'logger'):
                        self.logger.info("No website targets configured for monitoring")
                    time.sleep(30)
                    continue
                
                for target in targets:
                    if not self.monitoring_active:
                        break
                    try:
                        self.check_website(target)
                    except Exception as e:
                        if hasattr(self, 'logger'):
                            self.logger.error(f"Error checking website {target.get('url', 'unknown')}: {e}")
                        else:
                            print(f"Error checking website {target.get('url', 'unknown')}: {e}")
                    
                # Update performance stats
                self.performance_stats['websites_monitored'] = len(targets)
                
                # Wait for next check
                interval = self.config.get('monitoring', {}).get('website_check_interval', 5)
                time.sleep(max(1, interval))  # Minimum 1 second interval
                
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"Error in website monitoring loop: {e}")
                else:
                    print(f"Error in website monitoring loop: {e}")
                time.sleep(10)
                
    def check_website(self, target: Dict):
        """Check individual website status and security"""
        if not isinstance(target, dict) or 'url' not in target:
            if hasattr(self, 'logger'):
                self.logger.error(f"Invalid target format: {target}")
            return
            
        url = target['url']
        name = target.get('name', urlparse(url).netloc)
        start_time = time.time()
        
        try:
            # Configure session with reasonable timeouts
            session = requests.Session()
            session.headers.update({
                'User-Agent': self.config.get('website_monitoring', {}).get('user_agent', 
                    'Quantum Lock Security Monitor v3.0')
            })
            
            # Make request with error handling
            timeout = min(30, self.config.get('website_monitoring', {}).get('timeout', 10))  # Max 30 seconds
            response = session.get(
                url, 
                timeout=timeout, 
                verify=self.config.get('website_monitoring', {}).get('check_ssl', True),
                allow_redirects=self.config.get('website_monitoring', {}).get('follow_redirects', True)
            )
            
            response_time = round(time.time() - start_time, 3)
            
            # Analyze response
            analysis_result = self.analyze_website_response(
                url, name, response, response_time, start_time
            )
            
            # Store in database
            self.store_website_check(analysis_result)
            
            # Generate report entry
            self.add_website_report_entry(analysis_result)
            
            # Update performance stats
            self.performance_stats['website_checks'] += 1
            
        except requests.exceptions.RequestException as e:
            # Handle connection errors
            error_result = {
                'url': url,
                'name': name,
                'timestamp': datetime.now().isoformat(),
                'status_code': 0,
                'response_time': round(time.time() - start_time, 3),
                'is_accessible': False,
                'error_message': str(e)[:500],  # Limit error message length
                'threat_level': 'HIGH' if 'timeout' in str(e).lower() else 'MEDIUM',
                'ssl_valid': False
            }
            
            self.store_website_check(error_result)
            self.add_website_report_entry(error_result)
            
            if hasattr(self, 'logger'):
                self.logger.warning(f"Website check failed for {name}: {str(e)[:200]}")
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Unexpected error checking website {name}: {e}")
            
    def analyze_website_response(self, url: str, name: str, response: requests.Response, 
                                response_time: float, start_time: float) -> Dict:
        """Analyze website response for security and performance issues"""
        result = {
            'url': url,
            'name': name,
            'timestamp': datetime.now().isoformat(),
            'status_code': response.status_code,
            'response_time': response_time,
            'content_length': len(response.content) if response.content else 0,
            'is_accessible': True,
            'error_message': None,
            'threat_level': 'LOW',
            'ssl_valid': False,
            'ssl_expires': None,
            'redirect_url': None,
            'security_issues': [],
            'performance_issues': []
        }
        
        try:
            # Check status code
            expected_codes = self.config.get('website_monitoring', {}).get('expected_status_codes', [200])
            if response.status_code not in expected_codes:
                result['threat_level'] = 'MEDIUM'
                result['security_issues'].append(f"Unexpected status code: {response.status_code}")
            
            # Check response time
            warning_time = self.config.get('thresholds', {}).get('website_response_time_warning', 3.0)
            critical_time = self.config.get('thresholds', {}).get('website_response_time_critical', 10.0)
            
            if response_time >= critical_time:
                result['threat_level'] = 'HIGH'
                result['performance_issues'].append(f"Critical response time: {response_time}s")
            elif response_time >= warning_time:
                if result['threat_level'] == 'LOW':
                    result['threat_level'] = 'MEDIUM'
                result['performance_issues'].append(f"Slow response time: {response_time}s")
            
            # Check SSL certificate
            if url.startswith('https://'):
                try:
                    hostname = urlparse(url).hostname
                    if hostname:
                        context = ssl.create_default_context()
                        with socket.create_connection((hostname, 443), timeout=5) as sock:
                            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                                cert = ssock.getpeercert()
                                result['ssl_valid'] = True
                                # Parse certificate expiry
                                if 'notAfter' in cert:
                                    expires = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                                    result['ssl_expires'] = expires.isoformat()
                                    
                                    # Check if certificate expires soon
                                    days_until_expiry = (expires - datetime.now()).days
                                    if days_until_expiry <= 30:
                                        result['threat_level'] = 'HIGH'
                                        result['security_issues'].append(f"SSL certificate expires in {days_until_expiry} days")
                                    elif days_until_expiry <= 60:
                                        if result['threat_level'] == 'LOW':
                                            result['threat_level'] = 'MEDIUM'
                                        result['security_issues'].append(f"SSL certificate expires in {days_until_expiry} days")
                                        
                except Exception as e:
                    result['ssl_valid'] = False
                    result['security_issues'].append(f"SSL check failed: {str(e)[:100]}")
                    if result['threat_level'] == 'LOW':
                        result['threat_level'] = 'MEDIUM'
            
            # Check for redirects
            if response.history:
                result['redirect_url'] = response.url
                if len(response.history) > 3:
                    result['security_issues'].append(f"Multiple redirects detected: {len(response.history)}")
            
            # Content analysis (with safety checks)
            if response.content and len(response.content) < 1000000:  # Only analyze content < 1MB
                try:
                    content_text = response.text.lower()[:10000]  # Limit content analysis to first 10KB
                    
                    # Check for common error indicators
                    error_indicators = ['error', 'exception', 'stack trace', 'debug', 'sql error', 'database error']
                    for indicator in error_indicators:
                        if indicator in content_text:
                            result['security_issues'].append(f"Potential information disclosure: {indicator}")
                            if result['threat_level'] == 'LOW':
                                result['threat_level'] = 'MEDIUM'
                            break  # Only report first found indicator
                    
                    # Check for potential defacements
                    defacement_indicators = ['hacked', 'owned', 'defaced', 'anonymous', 'pwned']
                    for indicator in defacement_indicators:
                        if indicator in content_text:
                            result['threat_level'] = 'CRITICAL'
                            result['security_issues'].append(f"Potential website defacement detected: {indicator}")
                            break  # Only report first found indicator
                    
                    # Calculate content hash for change detection
                    result['content_hash'] = hashlib.md5(response.content[:50000]).hexdigest()  # Hash first 50KB
                    
                except UnicodeDecodeError:
                    # Handle binary content
                    result['content_hash'] = hashlib.md5(response.content[:50000]).hexdigest()
                except Exception as e:
                    if hasattr(self, 'logger'):
                        self.logger.debug(f"Content analysis error for {url}: {e}")
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error analyzing website response for {url}: {e}")
            result['error_message'] = f"Analysis error: {str(e)[:200]}"
        
        return result
        
    def store_website_check(self, result: Dict):
        """Store website check result in database"""
        if not hasattr(self, 'conn') or not self.conn:
            return
            
        try:
            with self._db_lock:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO website_monitoring 
                    (timestamp, website_url, status_code, response_time, content_hash, 
                     ssl_valid, ssl_expires, is_accessible, error_message, content_length, redirect_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result['timestamp'],
                    result['url'],
                    result['status_code'],
                    result['response_time'],
                    result.get('content_hash'),
                    result['ssl_valid'],
                    result.get('ssl_expires'),
                    result['is_accessible'],
                    result.get('error_message'),
                    result.get('content_length', 0),
                    result.get('redirect_url')
                ))
                self.conn.commit()
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to store website check result: {e}")
            
    def add_website_report_entry(self, result: Dict):
        """Add entry to the user-friendly website monitoring report"""
        report_file = self.config.get('reporting', {}).get('website_report_file', 
                                                          './reports.txt')
        
        try:
            # Ensure report directory exists
            Path(report_file).parent.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.fromisoformat(result['timestamp']).strftime('%B %d, %Y at %I:%M:%S %p')
            
            # Determine status emoji and message
            if not result['is_accessible']:
                status_emoji = "CRITICAL"
                status_msg = "WEBSITE DOWN"
                user_msg = f" {result['name']} is not accessible"
            elif result['threat_level'] == 'CRITICAL':
                status_emoji = "URGENT"
                status_msg = "CRITICAL ISSUE"
                user_msg = f" URGENT: Critical security issue detected on {result['name']}"
            elif result['threat_level'] == 'HIGH':
                status_emoji = "🟠"
                status_msg = "HIGH RISK"
                user_msg = f" High-risk issue detected on {result['name']}"
            elif result['threat_level'] == 'MEDIUM':
                status_emoji = "🟡"
                status_msg = "WARNING"
                user_msg = f" Warning: Issue detected on {result['name']}"
            else:
                status_emoji = "🟢"
                status_msg = "HEALTHY"
                user_msg = f"{result['name']} is operating normally"
            
            # Build detailed report entry
            report_entry = f"""
{'='*80}
{status_emoji} WEBSITE MONITORING REPORT - {status_msg}
{'='*80}
Timestamp: {timestamp}
Website: {result['name']}
URL: {result['url']}

 STATUS SUMMARY:
{user_msg}

 TECHNICAL DETAILS:
"""
            
            if result['is_accessible']:
                report_entry += f"""Status Code: {result['status_code']} {'OKAY' if result['status_code'] in [200, 301, 302] else 'NOT OKAY'}
Response Time: {result['response_time']} seconds {'OKAY' if result['response_time'] < 3.0 else 'ALERT️' if result['response_time'] < 10.0 else 'NOT OKAY'}
Content Size: {result.get('content_length', 0)} bytes
SSL Certificate: {' Valid' if result['ssl_valid'] else ' Invalid/Missing'}
"""
                
                if result.get('ssl_expires'):
                    try:
                        expires = datetime.fromisoformat(result['ssl_expires'])
                        days_left = (expires - datetime.now()).days
                        report_entry += f"SSL Expires: {expires.strftime('%B %d, %Y')} ({days_left} days remaining)\n"
                    except:
                        pass
                        
                if result.get('redirect_url') and result['redirect_url'] != result['url']:
                    report_entry += f"Final URL: {result['redirect_url']} (redirected)\n"
            else:
                report_entry += f"Error Message: {result.get('error_message', 'Unknown error')}\n"
                report_entry += f"Connection Failed: Website is not responding\n"
            
            # Add security and performance issues
            if result.get('security_issues'):
                report_entry += f"\n SECURITY ISSUES DETECTED:\n"
                for issue in result['security_issues']:
                    report_entry += f"• {issue}\n"
            
            if result.get('performance_issues'):
                report_entry += f"\n PERFORMANCE ISSUES:\n"
                for issue in result['performance_issues']:
                    report_entry += f"• {issue}\n"
            
            # Add recommendations
            report_entry += f"\n RECOMMENDATIONS:\n"
            if not result['is_accessible']:
                report_entry += "• Check if the website is down or experiencing technical difficulties\n"
                report_entry += "• Verify your internet connection\n"
                report_entry += "• Contact the website administrator if the issue persists\n"
            elif result['threat_level'] == 'CRITICAL':
                report_entry += "• IMMEDIATE ACTION REQUIRED: Website may be compromised\n"
                report_entry += "• Contact your security team or website administrator immediately\n"
                report_entry += "• Consider blocking access until the issue is resolved\n"
            elif result['threat_level'] == 'HIGH':
                report_entry += "• Review website security settings\n"
                report_entry += "• Monitor closely for additional issues\n"
                report_entry += "• Consider contacting the website administrator\n"
            elif result['threat_level'] == 'MEDIUM':
                report_entry += "• Monitor the situation\n"
                report_entry += "• Address performance or security warnings when possible\n"
            else:
                report_entry += "• Website is operating normally\n"
                report_entry += "• Continue regular monitoring\n"
            
            report_entry += f"\n{'='*80}\n\n"
            
            # Write to report file
            with open(report_file, 'a', encoding='utf-8') as f:
                f.write(report_entry)
                
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to write website report entry: {e}")

    def generate_website_summary_report(self):
        """Generate a summary report of all monitored websites"""
        if not hasattr(self, 'conn') or not self.conn:
            return
            
        try:
            with self._db_lock:
                cursor = self.conn.cursor()
                
                # Get recent website data (last 24 hours)
                since_time = (datetime.now() - timedelta(hours=24)).isoformat()
                cursor.execute('''
                    SELECT website_url, COUNT(*) as checks, 
                           AVG(response_time) as avg_response_time,
                           COUNT(CASE WHEN is_accessible = 0 THEN 1 END) as downtime_count,
                           MAX(timestamp) as last_check
                    FROM website_monitoring 
                    WHERE timestamp > ? 
                    GROUP BY website_url
                ''', (since_time,))
                
                websites = cursor.fetchall()
            
            if not websites:
                return
            
            report_file = self.config.get('reporting', {}).get('website_report_file', 
                                                              './reports.txt')
            
            # Ensure report directory exists
            Path(report_file).parent.mkdir(parents=True, exist_ok=True)
            
            summary_report = f"""
{'='*80}
 WEBSITE MONITORING - 24 HOUR SUMMARY REPORT
{'='*80}
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M:%S %p')}
Total Websites Monitored: {len(websites)}

 WEBSITE STATUS SUMMARY:
{'='*80}
"""
            
            for website in websites:
                url, checks, avg_time, downtime, last_check = website
                
                # Calculate uptime percentage
                uptime_percent = ((checks - downtime) / checks * 100) if checks > 0 else 0
                
                # Determine status
                if uptime_percent == 100:
                    status_emoji = "🟢"
                    status = "EXCELLENT"
                elif uptime_percent >= 95:
                    status_emoji = "🟡"
                    status = "GOOD"
                elif uptime_percent >= 90:
                    status_emoji = "🟠"
                    status = "WARNING"
                else:
                    status_emoji = "CRITICAL"
                    status = "POOR"
                
                try:
                    last_check_formatted = datetime.fromisoformat(last_check).strftime('%I:%M %p')
                except:
                    last_check_formatted = "Unknown"
                
                summary_report += f"""
{status_emoji} {urlparse(url).netloc}
   Status: {status} ({uptime_percent:.1f}% uptime)
   Average Response Time: {avg_time:.2f}s
   Total Checks: {checks}
   Downtime Events: {downtime}
   Last Checked: {last_check_formatted}
"""
            
            summary_report += f"\n{'='*80}\n\n"
            
            with open(report_file, 'a', encoding='utf-8') as f:
                f.write(summary_report)
                
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to generate website summary report: {e}")

    def is_valid_ip(self, ip_str: str) -> bool:
        """Check if string is a valid IP address"""
        try:
            ipaddress.ip_address(ip_str)
            return True
        except (ValueError, ipaddress.AddressValueError):
            return False

    def extract_ip_from_message(self, message: str) -> str:
        """Extract IP address from log message"""
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        matches = re.findall(ip_pattern, message)
        for match in matches:
            if self.is_valid_ip(match) and not match.startswith('127.'):
                return match
        return 'unknown'

    def log_security_event(self, event_type: str, threat_level: str, source_ip: str = None, 
                          target_ip: str = None, details: str = None, raw_log: str = None, 
                          timestamp: str = None):
        """Log security event to database and generate alerts"""
        if not hasattr(self, 'conn') or not self.conn:
            return
            
        try:
            if not timestamp:
                timestamp = datetime.now().isoformat()
            
            with self._db_lock:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO security_events 
                    (timestamp, event_type, threat_level, source_ip, target_ip, details, raw_log)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (timestamp, event_type, threat_level, source_ip, target_ip, details, raw_log))
                self.conn.commit()
            
            # Update performance stats
            self.performance_stats['events_processed'] += 1
            if threat_level in ['HIGH', 'CRITICAL']:
                self.performance_stats['threats_detected'] += 1
            
            # Log to console for immediate attention
            if threat_level in ['HIGH', 'CRITICAL'] and hasattr(self, 'logger'):
                self.logger.warning(f"THREAT DETECTED: {threat_level} - {event_type} from {source_ip}")
                
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to log security event: {e}")

    def block_ip_advanced(self, ip_address: str, reason: str, threat_level: str):
        """Advanced IP blocking with database tracking"""
        if not hasattr(self, 'conn') or not self.conn:
            return
            
        if ip_address in self.config.get('blocking', {}).get('whitelist_ips', []):
            if hasattr(self, 'logger'):
                self.logger.info(f"IP {ip_address} is whitelisted, not blocking")
            return
        
        try:
            with self._db_lock:
                cursor = self.conn.cursor()
                
                # Check if IP is already blocked
                cursor.execute('SELECT * FROM blocked_ips WHERE ip_address = ?', (ip_address,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing block
                    cursor.execute('''
                        UPDATE blocked_ips 
                        SET block_count = block_count + 1, last_blocked = ?, threat_level = ?
                        WHERE ip_address = ?
                    ''', (datetime.now().isoformat(), threat_level, ip_address))
                else:
                    # Insert new block
                    cursor.execute('''
                        INSERT INTO blocked_ips 
                        (ip_address, reason, threat_level, first_blocked, last_blocked)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (ip_address, reason, threat_level, datetime.now().isoformat(), datetime.now().isoformat()))
                
                self.conn.commit()
            
            self.blocked_ips.add(ip_address)
            self.performance_stats['ips_blocked'] += 1
            
            if hasattr(self, 'logger'):
                self.logger.warning(f"BLOCKED IP: {ip_address} for {reason} (threat level: {threat_level})")
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to block IP {ip_address}: {e}")

    def run_comprehensive_monitor(self):
        """Run the comprehensive monitoring system"""
        if hasattr(self, 'logger'):
            self.logger.info("STARTING: Comprehensive Security Monitoring System")
        else:
            print("STARTING: Comprehensive Security Monitoring System")
        
        try:
            # Start website monitoring
            self.start_website_monitoring()
            
            # Generate initial summary report
            self.generate_website_summary_report()
            
            # Main monitoring loop
            last_summary = time.time()
            
            while True:
                try:
                    # Run various monitoring tasks
                    if sys.platform.startswith('win'):
                        self.monitor_windows_security_events()
                        self.monitor_web_server_logs()
                    else:
                        # Linux/Unix monitoring could be added here
                        pass
                    
                    # Generate periodic summary reports (every hour)
                    if time.time() - last_summary > 3600:  # 1 hour
                        self.generate_website_summary_report()
                        last_summary = time.time()
                    
                    # Wait before next cycle
                    time.sleep(max(1, self.config.get('monitoring', {}).get('scan_interval', 30)))
                    
                except KeyboardInterrupt:
                    if hasattr(self, 'logger'):
                        self.logger.info("STOPPED: Monitoring stopped by user")
                    else:
                        print("STOPPED: Monitoring stopped by user")
                    break
                except Exception as e:
                    if hasattr(self, 'logger'):
                        self.logger.error(f"Error in monitoring loop: {e}")
                    else:
                        print(f"Error in monitoring loop: {e}")
                    time.sleep(10)
                    
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Critical error in comprehensive monitor: {e}")
            else:
                print(f"Critical error in comprehensive monitor: {e}")
        finally:
            self.stop_website_monitoring()
            if hasattr(self, 'logger'):
                self.logger.info("SHUTDOWN: Comprehensive Security Monitoring System stopped")
            else:
                print("SHUTDOWN: Comprehensive Security Monitoring System stopped")

    def monitor_windows_security_events(self):
        """Enhanced Windows Event Log monitoring"""
        if not sys.platform.startswith('win'):
            return
            
        try:
            # Query Security Event Log for authentication events
            powershell_cmd = """
            $StartTime = (Get-Date).AddMinutes(-30)
            Get-WinEvent -FilterHashtable @{LogName='Security'; StartTime=$StartTime; ID=@(4625,4648,4771,4776,4740,4624)} -MaxEvents 500 -ErrorAction SilentlyContinue |
            ForEach-Object {
                $TimeCreated = $_.TimeCreated.ToString('yyyy-MM-ddTHH:mm:ss')
                $EventId = $_.Id
                $Message = $_.Message -replace '[\\r\\n]+', ' '
                "$TimeCreated|$EventId|$Message"
            }
            """
            
            result = subprocess.run(
                ['powershell', '-Command', powershell_cmd],
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if '|' in line:
                        self.analyze_windows_security_event(line)
                        
        except subprocess.TimeoutExpired:
            if hasattr(self, 'logger'):
                self.logger.warning("Windows Event Log query timed out")
        except FileNotFoundError:
            if hasattr(self, 'logger'):
                self.logger.warning("PowerShell not found - Windows event monitoring disabled")
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error monitoring Windows security events: {e}")

    def analyze_windows_security_event(self, event_line: str):
        """Analyze Windows security event with enhanced detection"""
        try:
            parts = event_line.split('|', 2)
            if len(parts) < 3:
                return
                
            timestamp, event_id_str, message = parts
            
            try:
                event_id = int(event_id_str)
            except ValueError:
                return
            
            # Extract IP address and username
            source_ip = self.extract_ip_from_message(message)
            username = self.extract_username_from_message(message)
            
            # Determine threat level and action based on event ID
            threat_info = self.classify_windows_event(event_id, message)
            
            if threat_info:
                self.log_security_event(
                    event_type=threat_info['type'],
                    threat_level=threat_info['level'],
                    source_ip=source_ip,
                    details=threat_info['description'],
                    raw_log=message[:1000],  # Limit log size
                    timestamp=timestamp
                )
                
                # Update threat counters
                if source_ip and source_ip != 'unknown':
                    self.threat_counters[threat_info['type']][source_ip] += 1
                    
                    # Auto-block logic for brute force
                    max_failed_logins = self.config.get('thresholds', {}).get('max_failed_logins', 3)
                    if (threat_info['type'] == 'brute_force' and 
                        self.threat_counters['brute_force'][source_ip] >= max_failed_logins):
                        self.block_ip_advanced(source_ip, 'brute_force', 'HIGH')
                        
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.debug(f"Error analyzing Windows event: {e}")

    def classify_windows_event(self, event_id: int, message: str) -> Optional[Dict]:
        """Classify Windows security event"""
        classifications = {
            4625: {'type': 'brute_force', 'level': 'MEDIUM', 'description': 'Failed Windows login attempt'},
            4648: {'type': 'suspicious_login', 'level': 'LOW', 'description': 'Login with explicit credentials'},
            4771: {'type': 'brute_force', 'level': 'MEDIUM', 'description': 'Kerberos pre-authentication failed'},
            4776: {'type': 'brute_force', 'level': 'MEDIUM', 'description': 'Domain controller authentication failed'},
            4740: {'type': 'account_lockout', 'level': 'HIGH', 'description': 'User account locked out'},
            4624: {'type': 'successful_login', 'level': 'LOW', 'description': 'Successful login'}
        }
        
        base_info = classifications.get(event_id)
        if not base_info:
            return None
            
        # Enhance classification based on message content
        enhanced_info = base_info.copy()
        
        # Check for service accounts or suspicious usernames
        if re.search(r'(admin|administrator|root|sa|service)', message, re.IGNORECASE):
            enhanced_info['level'] = 'HIGH'
            enhanced_info['description'] += ' (privileged account)'
            
        return enhanced_info

    def extract_username_from_message(self, message: str) -> Optional[str]:
        """Extract username from Windows event message"""
        patterns = [
            r'Account Name:\s*([^\s\r\n]+)',
            r'User Name:\s*([^\s\r\n]+)',
            r'Target User Name:\s*([^\s\r\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                username = match.group(1).strip()
                if username and username != '-':
                    return username
        return None

    def monitor_web_server_logs(self):
        """Enhanced web server log monitoring"""
        if not sys.platform.startswith('win'):
            return
            
        iis_log_paths = [
            "C:\\inetpub\\logs\\LogFiles\\W3SVC1",
            "C:\\Windows\\System32\\LogFiles\\W3SVC1"
        ]
        
        for log_dir in iis_log_paths:
            if os.path.exists(log_dir):
                try:
                    log_files = sorted(
                        Path(log_dir).glob("*.log"), 
                        key=lambda x: x.stat().st_mtime, 
                        reverse=True
                    )[:2]  # Process last 2 log files
                    
                    for log_file in log_files:
                        self.analyze_web_log_advanced(str(log_file))
                        
                except Exception as e:
                    if hasattr(self, 'logger'):
                        self.logger.error(f"Error monitoring web logs in {log_dir}: {e}")

    def analyze_web_log_advanced(self, log_file: str):
        """Advanced web log analysis with threat correlation"""
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                # Read last 2000 lines efficiently
                lines = []
                for line in f:
                    lines.append(line)
                    if len(lines) > 2000:
                        lines.pop(0)  # Keep only last 2000 lines
                
            for line_num, line in enumerate(lines):
                if line.startswith('#') or not line.strip():
                    continue
                    
                # Parse IIS log line
                fields = line.split()
                if len(fields) < 10:
                    continue
                    
                # Extract key fields (typical IIS format)
                try:
                    timestamp = f"{fields[0]} {fields[1]}"
                    client_ip = fields[2] if self.is_valid_ip(fields[2]) else 'unknown'
                    method = fields[3] if len(fields) > 3 else 'GET'
                    uri = fields[4] if len(fields) > 4 else '/'
                    status_code = int(fields[5]) if len(fields) > 5 and fields[5].isdigit() else 0
                    user_agent = ' '.join(fields[9:]) if len(fields) > 9 else ''
                    
                    # Analyze for threats
                    self.analyze_web_request(
                        client_ip, method, uri, status_code, 
                        user_agent, line.strip()[:1000], timestamp  # Limit line length
                    )
                    
                except (IndexError, ValueError) as e:
                    continue
                    
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error analyzing web log {log_file}: {e}")

    def analyze_web_request(self, ip: str, method: str, uri: str, 
                           status: int, user_agent: str, raw_log: str, timestamp: str):
        """Analyze individual web request for threats"""
        threats_detected = []
        
        # Check for attack patterns in URI
        full_request = f"{method} {uri}"
        for attack_type, attack_info in self.suspicious_patterns.items():
            for pattern in attack_info['patterns']:
                try:
                    if re.search(pattern, full_request, re.IGNORECASE):
                        threats_detected.append({
                            'type': f'web_{attack_type}',
                            'level': attack_info['severity'],
                            'description': f"{attack_info['description']} in web request"
                        })
                        break  # Only report first match per attack type
                except re.error:
                    continue  # Skip invalid regex patterns
        
        # Log detected threats
        for threat in threats_detected:
            self.log_security_event(
                event_type=threat['type'],
                threat_level=threat['level'],
                source_ip=ip,
                details=f"{threat['description']}: {uri[:200]}",  # Limit URI length
                raw_log=raw_log,
                timestamp=timestamp
            )

    def display_status(self):
        """Display current system status"""
        print("\n" + "="*60)
        print("PROFESSIONAL BLUE TEAM SECURITY MONITOR STATUS")
        print("="*60)
        print(f"Version: {self.version}")
        print(f"Started: {self.startup_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Running as Admin: {'Yes' if self.is_admin else 'No'}")
        print(f"Website Monitoring: {'Active' if self.monitoring_active else 'Inactive'}")
        
        # Performance stats
        print("\n PERFORMANCE STATISTICS:")
        print("-" * 30)
        for key, value in self.performance_stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        
        # Website targets
        targets = self.config.get('website_monitoring', {}).get('targets', [])
        if targets:
            print(f"\n MONITORED WEBSITES ({len(targets)}):")
            print("-" * 30)
            for target in targets:
                print(f"• {target.get('name', 'Unknown')} - {target.get('url', 'No URL')}")
        else:
            print("\n No websites currently monitored")
        
        print("\n" + "="*60)


def safe_input(prompt: str, default: str = "") -> str:
    """Safe input function with encoding handling"""
    try:
        user_input = input(prompt).strip()
        return user_input if user_input else default
    except (UnicodeDecodeError, UnicodeEncodeError):
        print("Input encoding error - using default")
        return default
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return "quit"
    except Exception as e:
        print(f"Input error: {e}")
        return default


if __name__ == "__main__":
    # Set console encoding for Windows
    if sys.platform.startswith('win'):
        try:
            # For Windows 10 version 1903 and later
            os.system('chcp 65001 >nul 2>&1')
        except:
            pass
        
        # Try to reconfigure stdout for UTF-8
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass
    
    print("Professional Blue Team Security Monitor v3.0")
    print("=" * 60)
    
    try:
        monitor = ProfessionalBlueTeam()
        
        # Interactive setup for website monitoring
        print("\nWebsite Monitoring Setup")
        print("=" * 30)
        print("Enter websites to monitor (one at a time)")
        print("Examples: google.com, https://example.com")
        print("Type 'done' when finished, 'skip' to skip setup")
        
        website_count = 0
        while True:
            website = safe_input(f"\nEnter website URL #{website_count + 1} (or 'done'/'skip'): ")
            
            if website.lower() in ['done', 'quit']:
                break
            elif website.lower() == 'skip':
                print("Skipping website setup")
                break
            elif website:
                try:
                    name = safe_input(f"Enter friendly name for {website} (optional): ")
                    monitor.add_website_target(website, name if name else None)
                    print(f" Added {website} to monitoring list")
                    website_count += 1
                    
                    if website_count >= 10:  # Reasonable limit
                        print("Maximum of 10 websites reached")
                        break
                except Exception as e:
                    print(f" Error adding website: {e}")
            else:
                print("Please enter a valid website URL")
        
        # Display current configuration
        monitor.display_status()
        
        if website_count > 0:
            print(f"\n Starting monitoring system with {website_count} websites...")
            report_file = monitor.config.get('reporting', {}).get('website_report_file', './reports.txt')
            print(f" Reports will be saved to: {report_file}")
            print("️  Website checks every 5 seconds")
            print(" Summary reports generated hourly")
            print("\n️  Press Ctrl+C to stop monitoring")
        else:
            print("\n  No websites configured for monitoring")
            print(" System will monitor security events only")
            print("\n️  Press Ctrl+C to stop monitoring")
        
        print("\n" + "="*60)
        print("STARTING MONITORING...")
        print("="*60)
        
        # Start monitoring
        monitor.run_comprehensive_monitor()
        
    except KeyboardInterrupt:
        print("\n\ Monitoring stopped by user")
    except Exception as e:
        print(f"\n Critical Error: {e}")
        if 'monitor' in locals():
            try:
                monitor.logger.error(f"Critical startup error: {e}")
            except:
                pass
    finally:
        if 'monitor' in locals():
            try:
                monitor.stop_website_monitoring()
            except:
                pass
        print("\n Monitoring system shutdown complete")
        print("Thank you for using Professional Blue Team Security Monitor!")
