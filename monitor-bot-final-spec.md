# Monitor Bot — Final Architecture Spec

## Philosophy

- **Fail2Ban** → blocking and enforcement
- **Your Bot** → observing, notifying, and controlling
- **Nginx logs** → extended detection (scrapers, bad bots, rate spikes)

The bot is a **lean observability and control layer**, not a decision engine.
Fail2Ban already handles detection and banning — the bot's job is to surface
that activity to you in real time and give you a remote control panel via Telegram.

---

## What Fail2Ban Handles (Don't Rebuild This)

| Threat | Jail |
|---|---|
| SSH brute force | `sshd` |
| Bad bots / scrapers | `nginx-botsearch` |
| HTTP rate abuse | `nginx-limit-req` |
| Web auth failures | `nginx-http-auth` |
| Repeated 404s | `nginx-noscript` |
| Known bad bots | `nginx-badbots` |
| Repeat offenders | `recidive` |

Configure these in `jail.local`. Fail2Ban does the watching and banning.

---

## What the Bot Handles

### 1. Real-Time Telegram Notifications (Core Feature)
- IP banned → alert
- IP unbanned → alert
- Rate limit triggered → alert
- Suspicious user agent detected → alert
- Repeat offender flagged (banned more than once) → alert

### 2. Manual Control via Telegram Commands
```
/ban <ip>           → manually ban an IP via fail2ban
/unban <ip>         → manually unban
/whitelist <ip>     → add to whitelist (never gets banned)
/banned             → list currently banned IPs
/status             → fail2ban jail summary
/check <ip>         → show recent activity for an IP
```

### 3. Nginx Log Watching (Extended Detection)
Tail the Nginx access log and detect:
- High request frequency from a single IP
- Suspicious or unknown user agents
- Repeated hits on sensitive paths (`/admin`, `/wp-login`, `/.env`, etc.)
- Burst request patterns

On detection:
- **Auto-ban immediately via fail2ban-client** (24h, same as other bans)
- Send Telegram alert confirming the ban was applied

The notification is a **receipt**, not a request for action. If it was a false
positive, use `/unban <ip>` to reverse it immediately.

> **False positive protection:** thresholds are set high enough that no
> legitimate user ever triggers them. Whitelist your own IP and known crawlers
> (e.g. Googlebot ranges) in `whitelist.txt`.

### 4. Whitelist System
- Trusted IPs bypass all alerts and bans
- Stored in a flat file (`whitelist.txt`) — no database needed
- Respected by both the socket listener and the Nginx log watcher

### 5. Minimal State Tracking
Track only what's useful:
- Active bans (from fail2ban)
- Recent ban events (in memory or flat file)
- Repeat offenders (IP banned more than once)
- Your whitelist

---

## Event Flows

### Primary Flow (Fail2Ban events)
```
1. Fail2Ban detects attack and bans IP
2. Action script sends event to bot via Unix socket
3. Bot checks: is IP whitelisted? is it a repeat offender?
4. Bot sends Telegram alert with context
```

### Extended Flow (Nginx anomaly — auto-ban)
```
1. Nginx log shows rate spike, bad agent, or sensitive path hit
2. Bot detects anomaly via log tailer
3. Bot checks: is IP whitelisted? if yes → skip entirely
4. Bot bans IP immediately via fail2ban-client (24h)
5. Bot sends Telegram alert: "⚡ Auto-banned 1.2.3.4 — rate spike (120 req/30s)"
6. You can /unban <ip> instantly if it was a false positive
```

### Command Flow (You → Bot → Fail2Ban)
```
1. You send /ban 1.2.3.4 in Telegram
2. Bot receives command
3. Bot runs: fail2ban-client set <jail> banip 1.2.3.4
4. Bot replies: ✅ Banned 1.2.3.4
```

---

## File Structure

```
/opt/monitor-bot/
├── bot.py                   # entrypoint — starts socket listener + log watcher + telegram bot
├── config.py                # token, chat_id, socket path, watched paths, thresholds
├── requirements.txt
├── venv/
│
├── telegram/
│   ├── __init__.py
│   ├── notifier.py          # sends alerts to you
│   └── commands.py          # handles /ban /unban /whitelist etc.
│
├── fail2ban/
│   ├── __init__.py
│   ├── socket_listener.py   # receives ban/unban events from fail2ban
│   └── client.py            # wraps fail2ban-client CLI calls
│
├── nginx/
│   ├── __init__.py
│   └── log_watcher.py       # tails nginx access log, detects anomalies
│
└── store/
    ├── __init__.py
    └── whitelist.py         # reads/writes whitelist.txt

/etc/systemd/system/
└── monitor-bot.service

/etc/fail2ban/
├── jail.local
└── action.d/
    └── telegram-notify.conf

/run/monitor-bot/
└── bot.sock                 # Unix socket — fail2ban writes here, bot listens
```

---

## Integration: Fail2Ban → Bot

### Action file
Create `/etc/fail2ban/action.d/telegram-notify.conf`:

```ini
[Definition]
actionban   = echo '{"action":"ban","ip":"<ip>","jail":"<name>","failures":"<failures>"}' \
              | socat - UNIX-CONNECT:/run/monitor-bot/bot.sock

actionunban = echo '{"action":"unban","ip":"<ip>","jail":"<name>"}' \
              | socat - UNIX-CONNECT:/run/monitor-bot/bot.sock
```

### Attach to jails
In `/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
bantime  = 86400   # 24 hours — applies to all jails, fail2ban unbans automatically
findtime = 600
maxretry = 5
action   = %(action_)s
           telegram-notify

[sshd]
enabled = true

[nginx-badbots]
enabled = true

[nginx-botsearch]
enabled = true

[recidive]
enabled  = true
bantime  = 604800  # 7 days for repeat offenders
findtime = 86400
maxretry = 3
```

---

## Integration: Bot → Fail2Ban

The bot controls fail2ban via `fail2ban-client`. Wrap CLI calls in `fail2ban/client.py`:

```python
# fail2ban/client.py
import asyncio

DEFAULT_JAIL = "sshd"

async def ban_ip(ip: str, jail: str = DEFAULT_JAIL):
    await _run("set", jail, "banip", ip)

async def unban_ip(ip: str, jail: str = DEFAULT_JAIL):
    await _run("set", jail, "unbanip", ip)

async def add_ignoreip(ip: str, jail: str = DEFAULT_JAIL):
    await _run("set", jail, "addignoreip", ip)

async def get_banned(jail: str = DEFAULT_JAIL) -> str:
    return await _run("get", jail, "banned")

async def get_status(jail: str = DEFAULT_JAIL) -> str:
    return await _run("status", jail)

async def _run(*args) -> str:
    proc = await asyncio.create_subprocess_exec(
        "fail2ban-client", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(stderr.decode())
    return stdout.decode()
```

---

## Socket Listener

```python
# fail2ban/socket_listener.py
import asyncio
import json
import os

SOCKET_PATH = "/run/monitor-bot/bot.sock"

async def start(on_event):
    os.makedirs(os.path.dirname(SOCKET_PATH), exist_ok=True)
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    server = await asyncio.start_unix_server(
        lambda r, w: handle(r, w, on_event), path=SOCKET_PATH
    )
    os.chmod(SOCKET_PATH, 0o660)
    async with server:
        await server.serve_forever()

async def handle(reader, writer, on_event):
    try:
        data = await reader.read(1024)
        event = json.loads(data.decode())
        await on_event(event)
    except Exception as e:
        print(f"[SOCKET_ERR] {e}")
    finally:
        writer.close()
```

---

## Nginx Log Watcher

```python
# nginx/log_watcher.py
import asyncio
import re
from collections import defaultdict
from config import settings

REQUEST_THRESHOLD = 100       # requests per window — legitimate users never hit this
WINDOW_SECONDS   = 30
SENSITIVE_PATHS  = ["/admin", "/wp-login", "/.env", "/config", "/.git"]
BAD_AGENT_PATTERNS = re.compile(
    r"(sqlmap|nikto|masscan|zgrab|python-requests|curl|scrapy|semrush|ahrefsbot)",
    re.IGNORECASE
)

async def start(on_detect, whitelist):
    """
    on_detect(event) — called for every anomaly detected.
    The caller (bot.py) is responsible for banning + notifying.
    """
    counts = defaultdict(int)

    proc = await asyncio.create_subprocess_exec(
        "tail", "-F", "-n", "0", settings.NGINX_LOG_PATH,
        stdout=asyncio.subprocess.PIPE
    )

    async def reset_counts():
        while True:
            await asyncio.sleep(WINDOW_SECONDS)
            counts.clear()

    asyncio.create_task(reset_counts())

    async for line in proc.stdout:
        line = line.decode(errors="ignore")
        await analyze(line, counts, on_detect, whitelist)

async def analyze(line, counts, on_detect, whitelist):
    parts = line.split('"')
    if len(parts) < 4:
        return

    ip         = line.split()[0]
    request    = parts[1] if len(parts) > 1 else ""
    user_agent = parts[5] if len(parts) > 5 else ""

    if ip in whitelist:
        return

    counts[ip] += 1

    if counts[ip] == REQUEST_THRESHOLD:
        await on_detect({
            "type": "rate_spike",
            "ip": ip,
            "requests": counts[ip],
            "window": WINDOW_SECONDS
        })

    if any(path in request for path in SENSITIVE_PATHS):
        await on_detect({
            "type": "sensitive_path",
            "ip": ip,
            "path": request
        })

    if BAD_AGENT_PATTERNS.search(user_agent):
        await on_detect({
            "type": "bad_agent",
            "ip": ip,
            "agent": user_agent
        })
```

---

## Telegram Notifier

```python
# telegram/notifier.py
import httpx
from config import settings

BASE = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}"

async def send(text: str):
    async with httpx.AsyncClient() as client:
        await client.post(f"{BASE}/sendMessage", json={
            "chat_id": settings.CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        })

def format_ban(event: dict) -> str:
    return (
        f"🚨 *Banned* `{event['ip']}`\n"
        f"Jail: `{event.get('jail', 'unknown')}` | "
        f"Failures: `{event.get('failures', '?')}`"
    )

def format_unban(event: dict) -> str:
    return f"✅ *Unbanned* `{event['ip']}` from `{event.get('jail', 'unknown')}`"

def format_rate_spike(event: dict) -> str:
    return (
        f"⚡ *Auto-banned* `{event['ip']}`\n"
        f"Reason: rate spike — {event['requests']} requests in {event['window']}s\n"
        f"Duration: 24h | `/unban {event['ip']}` to reverse"
    )

def format_bad_agent(event: dict) -> str:
    return (
        f"🤖 *Auto-banned* `{event['ip']}`\n"
        f"Reason: bad bot — `{event.get('agent', '?')[:80]}`\n"
        f"Duration: 24h | `/unban {event['ip']}` to reverse"
    )

def format_sensitive_path(event: dict) -> str:
    return (
        f"👀 *Auto-banned* `{event['ip']}`\n"
        f"Reason: sensitive path — `{event.get('path', '?')}`\n"
        f"Duration: 24h | `/unban {event['ip']}` to reverse"
    )
```

---

## Entrypoint

```python
# bot.py
import asyncio
from config import settings
from store.whitelist import load_whitelist
from fail2ban.socket_listener import start as start_socket
from fail2ban.client import ban_ip, unban_ip, add_ignoreip, get_banned, get_status
from nginx.log_watcher import start as start_log_watcher
from telegram.notifier import send, format_ban, format_unban, \
    format_rate_spike, format_bad_agent, format_sensitive_path
from telegram.commands import start as start_commands

whitelist = load_whitelist()

async def on_fail2ban_event(event: dict):
    ip = event.get("ip")
    if ip in whitelist:
        return
    if event["action"] == "ban":
        await send(format_ban(event))
    elif event["action"] == "unban":
        await send(format_unban(event))

async def on_nginx_detect(event: dict):
    ip = event.get("ip")
    if not ip or ip in whitelist:
        return

    # Auto-ban immediately — notify after as a receipt
    try:
        await ban_ip(ip, jail="nginx-monitor")
    except Exception as e:
        print(f"[BAN_ERR] Could not ban {ip}: {e}")

    fmt = {
        "rate_spike":     format_rate_spike,
        "bad_agent":      format_bad_agent,
        "sensitive_path": format_sensitive_path,
    }.get(event["type"])
    if fmt:
        await send(fmt(event))

async def main():
    await asyncio.gather(
        start_socket(on_fail2ban_event),
        start_log_watcher(on_nginx_detect, whitelist),
        start_commands(ban_ip, unban_ip, add_ignoreip, get_banned, get_status, whitelist),
    )

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Systemd Service

Create `/etc/systemd/system/monitor-bot.service`:

```ini
[Unit]
Description=Monitor Bot — VPS Security Notifications
After=network.target fail2ban.service
Wants=fail2ban.service

[Service]
Type=simple
User=monitor-bot
Group=monitor-bot
WorkingDirectory=/opt/monitor-bot
ExecStart=/opt/monitor-bot/venv/bin/python bot.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/run/monitor-bot /opt/monitor-bot

[Install]
WantedBy=multi-user.target
```

---

## Setup Script

Create `setup.sh` at the project root:

```bash
#!/bin/bash
set -e

echo "[1/7] Installing system dependencies..."
apt update && apt install -y fail2ban socat python3-venv python3-pip

echo "[2/7] Creating system user..."
useradd --system --no-create-home --shell /usr/sbin/nologin monitor-bot || true

echo "[3/7] Deploying bot files..."
mkdir -p /opt/monitor-bot
cp -r . /opt/monitor-bot/
chown -R monitor-bot:monitor-bot /opt/monitor-bot

echo "[4/7] Creating virtualenv..."
python3 -m venv /opt/monitor-bot/venv
/opt/monitor-bot/venv/bin/pip install -r /opt/monitor-bot/requirements.txt

echo "[5/7] Creating socket directory..."
mkdir -p /run/monitor-bot
chown monitor-bot:monitor-bot /run/monitor-bot

echo "[6/7] Enabling services..."
systemctl daemon-reload
systemctl enable --now fail2ban
systemctl enable --now monitor-bot

echo "[7/7] Done."
echo "Edit /opt/monitor-bot/config.py with your TELEGRAM_TOKEN and CHAT_ID, then restart:"
echo "  systemctl restart monitor-bot"
```

---

## What to Remove From the Existing Codebase

- [ ] `app/mitigation.py` — delete entirely
- [ ] `Dockerfile` — delete
- [ ] `docker-compose.yml` — delete
- [ ] All imports of `FirewallMitigation` or `firewall_mitigation`
- [ ] `settings.BAN_ENABLED` and `settings.BAN_TIME`
- [ ] All `asyncio.create_subprocess_exec("iptables", ...)` calls
- [ ] All `asyncio.create_task(... unban ...)` scheduling logic

---

## What to Keep

- [x] Existing Telegram token and chat ID config
- [x] Any existing notification message formatting you like
- [x] Existing `config.py` structure (just add `NGINX_LOG_PATH`)

---

## Config Reference

```python
# config.py
class Settings:
    TELEGRAM_TOKEN : str = "your-token-here"
    CHAT_ID        : str = "your-chat-id-here"
    NGINX_LOG_PATH : str = "/var/log/nginx/access.log"
    SOCKET_PATH    : str = "/run/monitor-bot/bot.sock"
    WHITELIST_PATH : str = "/opt/monitor-bot/whitelist.txt"

settings = Settings()
```

---

## Ban Trigger Reference

| Trigger | Who bans | Ban duration | You see |
|---|---|---|---|
| Brute force, bad bots | fail2ban auto | 24h | 🚨 Banned alert |
| Rate spike, bad agent, sensitive path | bot auto (nginx watcher) | 24h | ⚡ Auto-banned alert |
| Repeat offender | fail2ban `recidive` auto | 7 days | 🚨 Banned alert |
| Unban | fail2ban auto on expiry | — | ✅ Unbanned alert |
| False positive reversal | You via `/unban` | — | — |
| Manual ban | You via `/ban` | 24h | — |

---

## Responsibility Map

| Concern | Owner |
|---|---|
| Brute force detection | fail2ban |
| Bad bot / scraper blocking | fail2ban (`nginx-badbots`, `nginx-botsearch`) |
| Rate limiting enforcement | fail2ban + nginx `limit_req_zone` |
| Ban / unban execution | fail2ban |
| Auto-unban after 24h | fail2ban |
| Repeat offender tracking | fail2ban (`recidive` jail) |
| Ban persistence across reboots | fail2ban |
| Real-time Telegram alerts | monitor-bot |
| Rate spike detection + auto-ban | monitor-bot (nginx log watcher) |
| Suspicious agent detection + auto-ban | monitor-bot (nginx log watcher) |
| Manual ban/unban/whitelist | monitor-bot (Telegram commands) |
| Whitelist persistence | flat file (`whitelist.txt`) |
| Process management | systemd |
