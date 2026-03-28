# 🧪 Security Bot Testing Guide

This guide explains how to test every part of your security bot, from local development to production on your VPS.

---

## 🏗️ 1. Local Testing (No Docker/Redis needed)
Use this when you want to quickly test the "Detection Logic" on your own computer.

### Step 1: Configuration
Ensure your `.env` has:
```env
MOCK_MODE=true
```

### Step 2: Running the integrated system
```bash
# Start the API and the Monitor in one go
python app/main.py
```

### Step 3: Run the simulation
In another terminal:
```bash
# This generates fake attacks in ./test_access.log
python scripts/test_sim.py

# To simulate a fake SSH attack, manually append to the log:
echo "Mar 25 10:00:00 srv sshd[123]: Failed password for root from 9.9.9.9 port 12345 ssh2" >> test_auth.log
# (Repeat 5 times to trigger a ban!)
```

---

## 🌍 2. Production Testing (On your VPS)
Use this after running `docker-compose up -d`.

### Step 1: Check your logs
```bash
# See the live feed from your bot (Nginx and SSH)
docker logs -f security_monitor
```

### Step 2: Force a "Real" Detection
From your own laptop, try to hit your VPS with a malicious header:

*   **Bad Bot Test**:
    ```bash
    curl -A "sqlmap/1.4" http://your_vps_ip/
    ```
*   **Sensitive Path Test**:
    ```bash
    curl http://your_vps_ip/.env
    ```
*   **Rate Limit Test**:
    (Run this multiple times quickly to hit the exact 5 threshold limit)
    ```bash
    for i in {1..10}; do curl -s http://your_vps_ip/ > /dev/null; done
    ```

*   **IPv6 Detection Test**:
    Ping the server repeatedly via your dual-stacked IPv6 proxy or home terminal to ensure your IPv6 `/64` subnet triggers botnet defenses flawlessly.

---

## 🖥️ 3. Whitelist Management (API Tools)
Test the ability to bypass the firewall for development or VIPs.

*   **View Whitelist**:
    `GET http://your_vps_ip:8000/api/v1/whitelist`
*   **Whitelist an IP**:
    `POST http://your_vps_ip:8000/api/v1/whitelist/YOUR_IP`
*   **Remove from Whitelist**:
    `DELETE http://your_vps_ip:8000/api/v1/whitelist/YOUR_IP`

## 🛡️ 4. Active Ban Controls (API Tools)
Verify that your API talks seamlessly with the kernel!

*   **View Banned IPs**:
    `GET http://your_vps_ip:8000/api/v1/banned-ips`
*   **Unban an IP**:
    `POST http://your_vps_ip:8000/api/v1/unban/YOUR_IP`
    *Note: Validating this directly checks whether your web app cleanly synchronizes Redis teardowns with active `iptables` daemon executions!*

---

## 📩 4. Alerting & Stats Monitoring
Confirm that your bot is talking to Telegram and tracking real-time data:

*   **Live Traffic & Block Stats**:
    Visit `http://your_vps_ip:8000/api/v1/stats`
    Keep this page open and run an attack from Postman; the numbers will increment automatically!

*   **HTML Telegram Alerts**:
    Check your Telegram chat for bold, formatted messages detailing the attack source and reason.

---

## 💾 5. Database Direct Access (Advanced)
If you want to view the raw tables:

*   **MySQL**: `docker exec -it security_mysql mysql -u security_user -p security_bot`
*   **Redis**: `docker exec -it security_redis redis-cli`
