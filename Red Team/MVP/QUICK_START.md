# Quick Start Guide - Red Team Attack System

## Get Started in 5 Minutes

### 1. **Install Dependencies**
```bash
cd MVP/backend
pip install -r requirements.txt
```

### 2. **Test the System**
```bash
# Test basic functionality
python debug_attacks.py

# Or run the simple test
python test_simple.py
```

### 3. **Start the Dashboard**
```bash
python app.py
```

### 4. **Access the Interface**
Open your browser and go to: `http://localhost:5000`

### 5. **Test with Safe Target**
- Enter: `http://httpbin.org` (safe test target)
- Click: "Initiate Red Team Attacks"
- Watch the logs for real-time progress

## If You Get Errors

### **Common Issues & Solutions:**

#### **Issue: "Module not found" errors**
```bash
# Solution: Install missing packages
pip install requests beautifulsoup4 dnspython python-whois
```

#### **Issue: "Permission denied" errors**
```bash
# Solution: Check file permissions
chmod +x red-team/attack/*.py
```

#### **Issue: "Import error" in attack modules**
```bash
# Solution: Run debug script to identify problems
python debug_attacks.py
```

#### **Issue: Web interface shows "Error running red team"**
```bash
# Solution: Check backend logs
tail -f backend/reports/logs.txt
```

## Testing Strategy

### **Phase 1: Basic Testing**
1. Use `http://httpbin.org` as target (always safe)
2. Run "Simple Test" attack first
3. Check logs for success/failure

### **Phase 2: Full Testing**
1. If basic tests pass, try real targets
2. Monitor logs for each attack module
3. Check for specific failure reasons

### **Phase 3: Troubleshooting**
1. Run `python debug_attacks.py`
2. Check individual module errors
3. Fix specific issues identified

## Understanding the Logs

### **Success Indicators:**
```
[SUCCESS] Simple Test: SUCCESS: Completed
[SUCCESS] Domain Reconnaissance: SUCCESS: Completed
```

### **Failure Indicators:**
```
[FAILED] Form Flooding: FAILED: Import error: No module named 'requests'
[FAILED] Server Clogging: FAILED: Script timed out after 2 minutes
```

### **System Messages:**
```
[START] Red Team attacks started on http://example.com
[TARGET] Target accessible (Status: 200)
[SUMMARY] Red Team attacks completed. Success: 3/5
[WARNING] 2 attacks failed. Check logs for details.
```

## Emergency Fixes

### **If Nothing Works:**
1. **Reset everything:**
   ```bash
   cd MVP
   rm -rf backend/reports/*
   python debug_attacks.py
   ```

2. **Check Python version:**
   ```bash
   python --version  # Should be 3.7+
   ```

3. **Verify file structure:**
   ```bash
   ls -la red-team/attack/
   ls -la backend/
   ```

### **Quick Health Check:**
```bash
# Test basic Python functionality
python -c "import requests; print('SUCCESS: requests works')"
python -c "import socket; print('SUCCESS: socket works')"

# Test attack module loading
python -c "import sys; sys.path.append('red-team'); import simple_test; print('SUCCESS: simple_test loads')"
```

## Success Criteria

### **System is Working When:**
- SUCCESS: `python debug_attacks.py` shows all modules pass
- SUCCESS: Web interface loads at `http://localhost:5000`
- SUCCESS: "Simple Test" attack executes successfully
- SUCCESS: Logs show real-time progress updates
- SUCCESS: At least 3/5 attack modules work

### **System Needs Fixing When:**
- FAILED: Import errors in debug script
- FAILED: Web interface shows "Error running red team"
- FAILED: No logs are generated
- FAILED: All attacks fail with same error

## Need Help?

1. **Run the debug script first:** `python debug_attacks.py`
2. **Check the logs:** `backend/reports/logs.txt`
3. **Verify dependencies:** `pip list | grep -E "(requests|beautifulsoup4|dnspython)"`
4. **Test individual modules:** `python red-team/attack/simple_test.py http://httpbin.org test.log`

---

**Remember**: Start with the simple test, then debug any issues before trying complex attacks!
