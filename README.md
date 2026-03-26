# 🛡️ Server Monitoring & Intrusion Detection Bot (Production Spec)

A professional, real-time NGINX and SSH log monitor that detects, alerts, and mitigates malicious activity using a high-performance asynchronous architecture.

---

## 🎯 Key Features

- **Real-Time Log Ingestion**: Concurrent monitoring of NGINX (`access.log`) and SSH (`auth.log`) streams.
- **Threat Detection Engine**:
    - **SSH Brute Force**: Detects and blocks multiple failed SSH login attempts.
    - **Botnet Detection**: Flags bursts of unique IPs from a single subnet (/24).
    - **Scraper Detection**: Blocks attempts to access sensitive files (`.env`, `.git`).
    - **Bad Bot Mitigation**: Blocks known malicious User-Agents including `sqlmap`, `nmap`.
    - **Rate Limiting**: Enforces requests-per-window thresholds (Default: 20req / 30s).
- **Dual Persistent Storage**:
    - **Redis**: Low-latency "Working Memory" for sliding-window detection, active bans, and **Live Traffic Stats**.
    - **MySQL**: Long-term persistent storage for attack history and **IP Whitelisting**.
- **Alert System**: Professional HTML-formatted Telegram notifications with detailed threat metadata.
- **Control API (FastAPI)**: REST endpoints for health stats, attack history, and **full Whitelist management**.

---

## 🚀 Deployment Guide

### 1. Prerequisites
- Docker & Docker Compose
- NGINX on host (logs at `/var/log/nginx/access.log`)
- SSH auth logs (typically at `/var/log/auth.log`)

### 2. Configure Environment
Create a `.env` file from the [template](file:///c:/Users/jqube/Documents/projects/bots/security-bot/.env.example) and fill in your details:
```env
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_id
MOCK_MODE=false
BAN_TIME=86400  # 24 hour default
```

### 3. Quick Start (Production)
Run the entire stack with a single command from the project root:
```bash
docker compose --env-file .env -f docker/docker-compose.yml up --build -d
```
*Docker will automatically initialize the MySQL schema, start the Monitor Worker & API, and mount your live logs.*

---

## 🧪 Testing & Development

### Local Test Mode (No Redis/MySQL needed)
1. Set `MOCK_MODE=true` in `.env`.
2. Start the integrated app: `python app/main.py`.
3. Run the simulator: `python scripts/test_sim.py`.

### Manual Controls via API
- **Live Stats**: `GET /api/v1/stats` (Real-time traffic and blocks)
- **Get Whitelist**: `GET /api/v1/whitelist`
- **Whitelist an IP**: `POST /api/v1/whitelist/{ip}`
- **Remove from Whitelist**: `DELETE /api/v1/whitelist/{ip}`
- **Unban an IP**: `POST /api/v1/unban/{ip}`

---

## 📁 Repository Structure
- `app/logs`: Watcher and Regex-based Parser.
- `app/detection`: Individual modular detection engines (Web & SSH).
- `app/storage`: Redis and MySQL database clients.
- `app/alerts`: Telegram service with HTML formatting.
- `workers/monitor.py`: The core monitoring background service.
- `docker/`: Full-stack Docker deployment configuration.
- `scripts/`: Initialization SQL and test simulation scripts.
- `testing.md`: [Full Testing Guide](file:///c:/Users/jqube/Documents/projects/bots/security-bot/testing.md).
- `walkthrough.md`: [System Architecture Walkthrough](file:///c:/Users/jqube/Documents/projects/bots/security-bot/walkthrough.md).
