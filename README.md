# 🛡️ Server Monitoring & Intrusion Detection Bot (Production Spec)

A professional, real-time NGINX log monitor that detects, alerts, and mitigates malicious activity using a high-performance asynchronous architecture.

---

## 🎯 Key Features

- **Real-Time Log Ingestion**: Uses async IO to stream NGINX logs with rotation support.
- **Threat Detection Engine**:
  - **Botnet Detection**: Flags bursts of unique IPs from a single subnet (/24).
  - **Scraper Detection**: Blocks attempts to access sensitive files (`.env`, `.git`) and high-diversity path scanning.
  - **Bad Bot Mitigation**: Blocks known malicious User-Agents including `sqlmap`, `nmap`, and `postman`.
  - **Rate Limiting**: Enforces requests-per-window thresholds (Default: 20req / 30s).
- **Dual Persistent Storage**:
  - **Redis**: Low-latency "Working Memory" for sliding-window detection and active bans.
  - **MySQL**: Long-term persistent storage for attack history and **IP Whitelisting**.
- **Alert System**: Professional HTML-formatted Telegram notifications with detailed threat metadata.
- **Control API (FastAPI)**: REST endpoints for health stats, attack history, and manual IP management.

---

## 🚀 Deployment Guide

### 1. Prerequisites

- Docker & Docker Compose
- NGINX on host (logs at `/var/log/nginx/access.log`)
- Python 3.11+ (for local testing)

### 2. Configure Environment

Create a `.env` file from the template and fill in your details:

```env
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_id

MOCK_MODE=false # Set to false for Production (MySQL/Redis)

# MySQL connection
MYSQL_HOST=mysql
MYSQL_USER=security_user
MYSQL_PASSWORD=password
MYSQL_DB=security_bot
```

### 3. Quick Start (Production)

Run the entire stack with a single command:

```bash
docker compose --env-file .env -f docker/docker-compose.yml up -d
```

_Docker will automatically initialize the MySQL schema and start the Monitor Worker & API._

---

## 🧪 Testing & Development

### Local Test Mode (No Redis/MySQL needed)

1. Set `MOCK_MODE=true` in `.env`.
2. Start the integrated app: `python app/main.py`.
3. Run the simulator: `python scripts/test_sim.py`.

### Manual Controls via API

- **See Attacks**: `GET /api/v1/attacks`
- **Whitelist an IP**: `POST /api/v1/whitelist/{ip}`
- **Unban an IP**: `POST /api/v1/unban/{ip}`

---

## 📁 Repository Structure

- `app/logs`: Watcher and Regex-based Parser.
- `app/detection`: Individual modular detection engines.
- `app/storage`: Redis and MySQL database clients.
- `app/alerts`: Telegram service with HTML formatting.
- `workers/monitor.py`: The core monitoring background service.
- `docker/`: Full-stack Docker deployment configuration.
- `scripts/`: Initialization SQL and test simulation scripts.
- `testing.md`: Full Testing Guide
