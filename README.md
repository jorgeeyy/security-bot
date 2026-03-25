# 🛡️ Server Monitoring & Intrusion Detection Bot (Production Spec)

A real-time NGINX log monitor that detects and automatically mitigates malicious activity.

## 🚀 Getting Started

### 1. Prerequisites
- Docker & Docker Compose
- Redis & MySQL (optional if running locally with MOCK_MODE)
- NGINX (with logs at `/var/log/nginx/access.log`)
- Python 3.11+

### 2. Configure Environment
Create a `.env` file from the template and fill in your details:
```bash
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
MOCK_MODE=false # Set to false for MySQL/Redis production usage
MYSQL_HOST=localhost
MYSQL_USER=security_user
MYSQL_PASSWORD=password
MYSQL_DB=security_bot
```

### 3. Quick Start (Docker)
```bash
docker-compose -f docker/docker-compose.yml up --build -d
```

### 4. Running Manually
```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis locally
redis-server

# Run the API
python app/main.py

# Run the Monitor Worker
python workers/monitor.py
```

## 🎯 Features
- **Real-Time Log Ingestion**: Uses async IO to stream NGINX logs.
- **Botnet Detection**: Bursts from subnets (/24) within a sliding window.
- **Scraper Detection**: Blocks access to sensitive files (`.env`, `.git`) and high diversity visits.
- **Bad Bot Mitigation**: Blocks known malicious User-Agents (`sqlmap`, `nmap`, etc.).
- **Rate Limit Enforcement**: Configurable thresholds for request bursts.
- **Telegram Integration**: Structured alerts for every threat detected and ban action.
- **Auto-Mitigation**: Banning via `iptables` (requires root/NET_ADMIN).

## 📊 API Endpoints
- `GET /api/v1/stats`: Current monitoring status.
- `GET /api/v1/attacks`: Recent threat history.
- `GET /api/v1/banned-ips`: List of currently blocked IPs.

## 📁 Project Structure
- `app/logs`: Watcher and Regex-based Parser.
- `app/detection`: Individual modular detection engines.
- `app/alerts`: Telegram service.
- `app/mitigation`: Iptables/Firewall interface.
- `workers/monitor.py`: The core monitoring service.
- `docker/`: Deployment configuration.
