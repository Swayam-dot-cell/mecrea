import subprocess
from flask import Flask, jsonify, request, send_from_directory
from datetime import datetime
import os
import sys
import traceback

# Import utility modules with error handling
try:
    from report_utils import save_json_report, generate_pdf_report
    from ai_utils import generate_ai_insights
except ImportError as e:
    print(f"Warning: Could not import utility modules: {e}")
    # Create dummy functions if imports fail
    def save_json_report(data, filename):
        print(f"Would save JSON report: {filename}")
    def generate_pdf_report(data, filename):
        print(f"Would save PDF report: {filename}")
    def generate_ai_insights(logs):
        return ["AI insights not available due to import error"]

app = Flask(__name__, static_folder="static", static_url_path="")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORTS_DIR = os.path.join(BASE_DIR, "backend", "reports")
LOG_FILE = os.path.join(REPORTS_DIR, "logs.txt")

os.makedirs(REPORTS_DIR, exist_ok=True)

# ---------------------------
# Utility functions
# ---------------------------
def log_event(message):
    """Append timestamped events into logs.txt"""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except Exception as e:
        print(f"Error writing to log: {e}")

def test_target_accessibility(target_url):
    """Test if the target URL is accessible"""
    try:
        import requests
        response = requests.get(target_url, timeout=10)
        return True, f"Target accessible (Status: {response.status_code})"
    except Exception as e:
        return False, f"Target not accessible: {str(e)}"

def run_attack_script(script_path, target_url, log_file):
    """Execute attack scripts and capture their output"""
    try:
        # Check if script exists
        if not os.path.exists(script_path):
            error_msg = f"Script not found: {script_path}"
            log_event(f"[ERROR] {error_msg}")
            return f"FAILED: {error_msg}"
        
        # Add the red-team directory to Python path so imports work
        red_team_dir = os.path.join(BASE_DIR, "red-team")
        env = os.environ.copy()
        
        # Handle different OS path separators
        if os.name == 'nt':  # Windows
            env['PYTHONPATH'] = f"{red_team_dir};{env.get('PYTHONPATH', '')}"
        else:  # Unix/Linux/Mac
            env['PYTHONPATH'] = f"{red_team_dir}:{env.get('PYTHONPATH', '')}"
        
        log_event(f"[EXEC] Executing: {os.path.basename(script_path)}")
        
        # Run the script with the target URL and log file
        result = subprocess.run(
            [sys.executable, script_path, target_url, log_file],
            capture_output=True, 
            text=True, 
            check=False,
            env=env,
            cwd=red_team_dir,
            timeout=120  # 2 minute timeout per attack
        )
        
        output = result.stdout.strip() if result.stdout else ""
        error = result.stderr.strip() if result.stderr else ""
        
        # Log both stdout and stderr
        if output:
            log_event(f"[OUTPUT] {output[:200]}...")  # Truncate long output
        if error:
            log_event(f"[ERROR] {error[:200]}...")  # Truncate long error
            
        # Determine success/failure
        if result.returncode == 0 and not error:
            return f"SUCCESS: {output[:100] if output else 'Completed'}"
        else:
            return f"FAILED: Return code {result.returncode}, Error: {error[:100] if error else 'Unknown error'}"
        
    except subprocess.TimeoutExpired:
        error_msg = f"Script timed out after 2 minutes: {os.path.basename(script_path)}"
        log_event(f"[TIMEOUT] {error_msg}")
        return f"FAILED: {error_msg}"
    except Exception as e:
        error_msg = f"Error executing {os.path.basename(script_path)}: {str(e)}"
        log_event(f"[ERROR] {error_msg}")
        return f"FAILED: {error_msg}"

def run_script(script_path, args=[]):
    """Execute external Python scripts safely"""
    try:
        if not os.path.exists(script_path):
            return f"FAILED: Script not found: {script_path}"
            
        result = subprocess.run(
            [sys.executable, script_path] + args,
            capture_output=True, text=True, check=False, timeout=60
        )
        return result.stdout.strip() if result.stdout else "Executed"
    except Exception as e:
        return f"FAILED: {str(e)}"

# ---------------------------
# Routes
# ---------------------------
@app.route("/run_red_team", methods=["POST"])
def run_red_team():
    try:
        target = request.json.get("target", "http://example.com")
        log_event(f"[START] Red Team attacks started on {target}")
        
        # Test target accessibility first
        accessible, message = test_target_accessibility(target)
        log_event(f"[TARGET] {message}")
        
        if not accessible:
            log_event(f"[ERROR] Cannot proceed with attacks - target not accessible")
            return jsonify({
                "message": "Red Team attacks failed - target not accessible", 
                "target": target,
                "status": "failed",
                "reason": "Target not accessible"
            }), 400

        attacks = {
            "Simple Test": os.path.join(BASE_DIR, "red-team/attack/simple_test.py"),
            "Domain Reconnaissance": os.path.join(BASE_DIR, "red-team/attack/getdomain.py"),
            "Form Flooding": os.path.join(BASE_DIR, "red-team/attack/formflooding.py"),
            "Honeytoken Deployment": os.path.join(BASE_DIR, "red-team/attack/honeytoken.py"),
            "Passive Reconnaissance": os.path.join(BASE_DIR, "red-team/attack/passiverecon.py"),
            "Server Clogging": os.path.join(BASE_DIR, "red-team/attack/serverclog.py"),
        }

        successful_attacks = 0
        failed_attacks = 0
        attack_results = {}

        for name, script in attacks.items():
            log_event(f"[EXEC] Executing {name} attack...")
            output = run_attack_script(script, target, LOG_FILE)
            
            # Track success/failure
            if output.startswith("SUCCESS"):
                successful_attacks += 1
                log_event(f"[SUCCESS] {name}: {output}")
            else:
                failed_attacks += 1
                log_event(f"[FAILED] {name}: {output}")
            
            attack_results[name] = output

        # Summary
        total_attacks = len(attacks)
        log_event(f"[SUMMARY] Red Team attacks completed. Success: {successful_attacks}/{total_attacks}")
        
        if failed_attacks > 0:
            log_event(f"[WARNING] {failed_attacks} attacks failed. Check logs for details.")
        
        return jsonify({
            "message": f"Red Team attacks completed. Success: {successful_attacks}/{total_attacks}", 
            "target": target,
            "status": "completed",
            "successful": successful_attacks,
            "failed": failed_attacks,
            "total": total_attacks,
            "results": attack_results
        })
        
    except Exception as e:
        error_msg = f"Critical error in Red Team execution: {str(e)}"
        log_event(f"[CRITICAL] {error_msg}")
        log_event(f"[TRACEBACK] {traceback.format_exc()}")
        return jsonify({
            "message": "Red Team attacks failed due to system error",
            "error": error_msg,
            "status": "error"
        }), 500

@app.route("/run_blue_team", methods=["POST"])
def run_blue_team():
    try:
        log_event("[START] Blue Team defenses started.")

        defenses = {
            "Add WAF Rule": os.path.join(BASE_DIR, "blue-team/add_waf_rule.py"),
            "Block IP": os.path.join(BASE_DIR, "blue-team/block_ip.py"),
            "Rate Limiting": os.path.join(BASE_DIR, "blue-team/rate_limit.py"),
        }

        successful_defenses = 0
        failed_defenses = 0

        for name, script in defenses.items():
            output = run_script(script)
            if output.startswith("FAILED"):
                failed_defenses += 1
                log_event(f"[FAILED] Blue Team: {name} -> {output}")
            else:
                successful_defenses += 1
                log_event(f"[SUCCESS] Blue Team: {name} -> {output}")

        log_event(f"[SUMMARY] Blue Team defenses completed. Success: {successful_defenses}/{len(defenses)}")
        
        return jsonify({
            "message": f"Blue Team defenses completed. Success: {successful_defenses}/{len(defenses)}",
            "status": "completed",
            "successful": successful_defenses,
            "failed": failed_defenses
        })
        
    except Exception as e:
        error_msg = f"Critical error in Blue Team execution: {str(e)}"
        log_event(f"[CRITICAL] {error_msg}")
        return jsonify({
            "message": "Blue Team defenses failed due to system error",
            "error": error_msg,
            "status": "error"
        }), 500

@app.route("/logs")
def get_logs():
    """Return plain text logs for UI console"""
    try:
        if not os.path.exists(LOG_FILE):
            return jsonify({"logs": "No logs available yet."})
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs_content = f.read()
            return jsonify({"logs": logs_content})
    except Exception as e:
        return jsonify({"logs": f"Error reading logs: {str(e)}"})

@app.route("/generate_report", methods=["POST"])
def generate_report():
    """Generate JSON + PDF reports with AI insights"""
    try:
        if not os.path.exists(LOG_FILE):
            return jsonify({"error": "No logs found"}), 400

        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = f.read()

        try:
            ai_suggestions = generate_ai_insights(logs)
        except:
            ai_suggestions = ["AI insights not available"]

        report_data = {
            "attack_summary": [line for line in logs.splitlines() if "Red Team" in line],
            "defense_summary": [line for line in logs.splitlines() if "Blue Team" in line],
            "ai_suggestions": ai_suggestions,
            "metadata": {
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_lines": len(logs.splitlines())
            }
        }

        # Save reports
        save_json_report(report_data, "final_report.json")
        generate_pdf_report(report_data, "final_report.pdf")

        log_event("[SUCCESS] Reports generated successfully.")
        return jsonify({"message": "Reports generated successfully."})
        
    except Exception as e:
        error_msg = f"Error generating report: {str(e)}"
        log_event(f"[ERROR] {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route("/download/<path:filename>")
def download_report(filename):
    """Download files from reports directory"""
    try:
        return send_from_directory(REPORTS_DIR, filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": f"File not found: {filename}"}), 404

# Serve index.html for frontend
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# ---------------------------
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
