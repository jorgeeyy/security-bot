# 🛡️ Security Bot 

A lightweight, native host-based observability and control layer built on top of **Fail2Ban**. This Python bot provides real-time Telegram notifications when threats are detected and allows you to instantly manage your server's security via Telegram commands.

---

## 🏗️ Architecture

Instead of reinventing the wheel with Docker, Redis, and MySQL, this bot natively integrates with your Linux host.
- **Fail2Ban** acts as the *Muscle*, securely parsing SSH and standard Nginx logs and applying kernel-level `iptables/UFW` blocks.
- **Security-Bot** acts as the *Brain*, listening to Fail2Ban's Unix socket to alert you on Telegram via Long Polling, and running advanced anomaly detection on your `access.log`.

### Key Features
1. **Real-Time Alerts:** Get instant Telegram notifications when an IP is banned, unbanned, or violates a strict HTTP rate threshold.
2. **Advanced Scraper Detection:** While Fail2Ban perfectly traps SSH brute-forcers, this bot tails your Nginx logs to catch API rate-spikes, sensitive path scraping (`/.env`, `/.git`), and malicious User-Agents, passing them to Fail2Ban instantly.
3. **Telegram Command Center:** Issue remote commands straight from your phone: `/ban`, `/unban`, `/whitelist`, `/status`, and `/banned`.

---

## 🛠️ Repository Structure

*   `bot.py`: Main entrypoint handling Long-Polling and thread delegation.
*   `config.py`: Environment configurations and path mappings.
*   `fail2ban/`: Connects the bot directly to the `/run/security-bot/bot.sock` Unix socket and wraps root OS `fail2ban-client` commands.
*   `nginx/`: Custom `log_watcher` tracking anomalous activity natively using in-memory queues (bypassing Redis dependencies).
*   `store/`: Native flat-file reading tracking trusted IP addresses.
*   `telegram/`: HTTP web-request handling and formatted notification engines.
*   `deploy/`: Infrastructure configuration including `jail.local`, `systemd` supervisors, and the complete `setup.sh` provisioning script.

---

## 🚀 Deployment Guide

### Prerequisites
- A Linux VPS (Ubuntu/Debian recommended).
- NGINX on host (routing logs to `/var/log/nginx/access.log`).
- `sudo` (root) privileges on the server.
- A Telegram Bot Token from **@BotFather** and your Chat ID from **@userinfobot**.

### 1. Configure Credentials
Prior to, or immediately after deployment, edit `/opt/security-bot/config.py` on your server to include your respective IDs:
```python
TELEGRAM_TOKEN : str = "1234567:ABCDEF-GHIJKL"
CHAT_ID        : str = "123456789"
```

### 2. Auto-Provision the Server
From the root of the project folder on your VPS, run the deployment shell script:
```bash
sudo bash deploy/setup.sh
```
*Note: This script will natively install Python 3 venv, create a secured `security-bot` system user, provision `/etc/sudoers.d/`, install and enable `fail2ban`, mount the unix sockets, and seamlessly kickstart the systemd service all in one motion.*

*(You can also use `sudo bash deploy/setup.sh 4 8` to selectively run chunks of the install loop!)*

### 3. Setup Telegram Commands
Open Telegram, navigate to **@BotFather**, type `/setcommands`, and paste the following natively into your chat to bind the UI menu:
```text
ban - Manually ban an IP via fail2ban
unban - Manually unban an IP
whitelist - Add an IP to the whitelist
banned - List currently banned IPs
status - Show fail2ban jail summary
```

Enjoy your fully automated, absolutely locked-down Linux server!
