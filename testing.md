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
```

---

## 🌍 2. Production Testing (On your VPS)
Use this after running `docker-compose up -d`.

### Step 1: Check your logs
```bash
# See the live feed from your bot
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
    (Run this multiple times quickly)
    ```bash
    for i in {1..35}; do curl -s http://your_vps_ip/ > /dev/null; done
    ```

---

## 📩 3. Alerting Tests (Telegram)
Confirm that your bot is actually talking to Telegram:
- On every detection, you should receive a structured notification in your chat.
- If it fails, check the logs for `[TELEGRAM_ERR]`.
- I've enabled **HTML parse mode**, so your messages will look bold and formatted.

---

## 🛡️ 4. Whitelist & Unban Testing
Testing the "Manual Override" features:

### Step 1: Whitelist yourself
If you don't want to be detected as a "Bad Bot" (e.g., when using Postman), run this:
```bash
curl -X POST http://your_vps_ip:8000/api/v1/whitelist/YOUR_IP
```
*Wait 1 minute, and now your IP will be ignored by the bot indefinitely.*

### Step 2: Unban an IP
If you accidentally ban a user during your tests, use the API to let them back in:
```bash
curl -X POST http://your_vps_ip:8000/api/v1/unban/IP_ADDRESS
```

---

## 📊 5. Analytics & Dashboard Testing
You can check the "History" at any time via your FastAPI endpoints:

- **Attacks History**: [http://your_vps_ip:8000/api/v1/attacks](http://your_vps_ip:8000/api/v1/attacks)
- **Banned IP List**: [http://your_vps_ip:8000/api/v1/banned-ips](http://your_vps_ip:8000/api/v1/banned-ips)
- **System Stats**: [http://your_vps_ip:8000/api/v1/stats](http://your_vps_ip:8000/api/v1/stats)
