# Quantumlock - Red Team Attack Dashboard

A comprehensive Red Team penetration testing platform with automated attack capabilities and real-time monitoring.

## Features

### Red Team Attacks
- **Domain Reconnaissance**: WHOIS lookup, DNS enumeration, IP geolocation
- **Form Flooding**: Automated form submission attacks with realistic data
- **Server Clogging**: HTTP GET flood attacks with multiple threads
- **Passive Reconnaissance**: Directory discovery, robots.txt analysis, search engine indexing
- **Honeytoken Deployment**: Strategic honeytoken placement across multiple endpoints

### Blue Team Defenses
- WAF rule management
- IP blocking capabilities
- Rate limiting implementation

### Real-time Monitoring
- Live attack logs
- Progress tracking
- Auto-refresh capabilities
- Comprehensive reporting

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd MVP
   ```

2. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Start the application**
   ```bash
   python app.py
   ```

4. **Access the dashboard**
   Open your browser and navigate to `http://localhost:5000`

## Usage

### Setting Up a Target
1. Enter the target URL in the "Target URL" field
2. Click "Save Target" to confirm
3. Ensure the target is accessible and you have permission to test it

### Running Red Team Attacks
1. Click the "Initiate Red Team Attacks" button
2. The system will execute all attack modules sequentially
3. Monitor progress in real-time through the logs
4. Attacks will automatically log their results

### Monitoring Attacks
- **Real-time Logs**: View attack progress and results
- **Auto-refresh**: Enable automatic log updates every 3 seconds
- **Manual Refresh**: Click "Refresh Logs" for immediate updates
- **Clear Logs**: Remove all log entries if needed

### Generating Reports
1. Click "Generate Report" after attacks complete
2. Download PDF or JSON reports
3. Reports include AI-generated insights and attack summaries

## Attack Modules

### 1. Domain Reconnaissance (`getdomain.py`)
- Extracts domain information from URLs
- Performs WHOIS lookups
- Resolves DNS records
- Retrieves IP geolocation data

### 2. Form Flooding (`formflooding.py`)
- Generates realistic fake user data
- Submits forms to multiple endpoints
- Uses threading for concurrent attacks
- Configurable request counts and delays

### 3. Server Clogging (`serverclog.py`)
- HTTP GET flood attacks
- Multiple thread support
- Rotating user agents
- Cache-busting parameters

### 4. Passive Reconnaissance (`passiverecon.py`)
- Robots.txt analysis
- Wayback Machine queries
- Search engine indexing checks
- Common directory discovery

### 5. Honeytoken Deployment (`honeytoken.py`)
- Creates unique honeytokens
- Submits to multiple form types
- Tracks submission success rates
- Strategic placement across endpoints

## Important Notes

### Legal and Ethical Considerations
- **ONLY test targets you own or have explicit permission to test**
- This tool is for educational and authorized security testing purposes
- Unauthorized attacks are illegal and unethical
- Always follow responsible disclosure practices

### Safety Features
- Attacks are designed to be non-destructive
- Rate limiting prevents overwhelming targets
- Configurable delays between requests
- Safe test targets available for validation

### Performance
- Attacks run sequentially to avoid overwhelming targets
- Configurable thread counts and request limits
- Progress tracking and real-time feedback
- Comprehensive logging for analysis

## Testing

### Test the System Safely
```bash
# Run the test suite
python test_attacks.py

# This will test all modules against httpbin.org (safe target)
```

### Validate Individual Modules
```bash
# Test specific attack modules
cd red-team/attack
python getdomain.py http://httpbin.org
python formflooding.py http://httpbin.org
```

## Logging and Monitoring

### Log Files
- **Main Logs**: `backend/reports/logs.txt`
- **Individual Attack Logs**: Generated per attack module
- **Real-time Display**: Web interface shows live updates

### Log Format
```
[2024-01-01 12:00:00] Red Team attacks started on http://example.com
[2024-01-01 12:00:01] Executing Form Flooding attack...
[2024-01-01 12:00:02] Red Team executed: Form Flooding -> Executed
```

## Security Considerations

### Network Security
- Use VPN when testing external targets
- Monitor network traffic for anomalies
- Implement proper firewall rules

### Target Protection
- Test against isolated environments
- Use rate limiting and monitoring
- Implement proper logging and alerting

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all dependencies are installed
2. **Permission Denied**: Check file permissions and Python path
3. **Network Errors**: Verify target accessibility and firewall rules
4. **Module Failures**: Check individual module logs for specific errors

### Debug Mode
- Enable Flask debug mode in `app.py`
- Check console output for detailed error messages
- Review individual attack module logs

## Configuration

### Attack Parameters
- Modify attack intensity in individual module files
- Adjust thread counts and request delays
- Configure target-specific parameters

### Logging Options
- Change log file locations
- Modify log format and detail level
- Configure log rotation and retention

## Contributing

### Adding New Attacks
1. Create new module in `red-team/attack/`
2. Implement `run(url, log_file)` function
3. Add to attack list in `app.py`
4. Update requirements.txt if needed

### Improving Existing Modules
- Enhance error handling
- Add new attack vectors
- Optimize performance
- Improve logging and reporting

## License

This project is for educational and authorized security testing purposes only. Users are responsible for ensuring they have proper authorization before testing any targets.

## Quick Start

1. **Install**: `pip install -r requirements.txt`
2. **Run**: `python app.py`
3. **Access**: `http://localhost:5000`
4. **Target**: Enter your test URL
5. **Attack**: Click "Initiate Red Team Attacks"
6. **Monitor**: Watch real-time logs
7. **Report**: Generate comprehensive reports

---

**Remember**: Always test responsibly and only against authorized targets!
