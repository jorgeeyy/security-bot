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

    # Use default windows command if not on linux
    import os
    if os.name == 'nt':
        print("[WARN] Using powershell tail for log_watcher on Windows")
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-c", f"Get-Content {settings.NGINX_LOG_PATH} -Wait -Tail 0",
            stdout=asyncio.subprocess.PIPE
        )
    else:
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
