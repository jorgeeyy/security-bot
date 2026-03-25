import os
import sys
import asyncio
import time

# Add the project root to sys.path to allow absolute imports like 'from app...'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.logs.watcher import LogWatcher
from app.logs.parser import LogParser
from app.detection.badbot import BadBotDetector
from app.detection.scraper import ScraperDetector
from app.detection.rate_limit import RateLimitDetector
from app.detection.botnet import BotnetDetector
from app.detection.ssh_bruteforce import SSHDetector
from app.alerts.telegram import telegram_alert_service
from app.mitigation.firewall import firewall_mitigation
from app.storage.redis_client import redis_client
from app.storage.mysql_client import mysql_client
from app.config import settings

class MonitorWorker:
    def __init__(self):
        self.watcher = LogWatcher()

    async def run(self):
        print("[MONITOR] Starting security monitoring worker...")
        # Now watching both Nginx and SSH logs
        await self.watcher.watch_all_logs(self.on_nginx_line, self.on_ssh_line)

    async def on_nginx_line(self, line: str):
        parsed = LogParser.parse_line(line)
        if not parsed:
            return

        ip = parsed["ip"]
        ua = parsed["user_agent"]
        path = parsed["path"]
        timestamp = time.time()

        if await self._should_skip(ip):
            return

        threat = None
        details = None
        
        # 1. Bad Bot Check
        is_bad_bot, msg = BadBotDetector.is_bad_bot(ua)
        if is_bad_bot:
            threat, details = "BAD BOT DETECTED", msg
        
        # 2. Scraper Check
        if not threat:
            is_scraper, msg = ScraperDetector.is_scraper(path)
            if is_scraper:
                threat, details = "SCRAPER DETECTED", msg
            else:
                is_div, msg = await ScraperDetector.check_path_diversity(ip, path, redis_client)
                if is_div:
                    threat, details = "SCRAPER (HIGH DIVERSITY) DETECTED", msg

        # 3. Rate Limit Check
        if not threat:
            is_rate, msg = await RateLimitDetector.is_rate_limited(ip, timestamp)
            if is_rate:
                threat, details = "RATE LIMIT EXCEEDED", msg

        # 4. Botnet Check
        if not threat:
            is_botnet, msg = await BotnetDetector.is_botnet_activity(ip, timestamp)
            if is_botnet:
                threat, details = "BOTNET ACTIVITY DETECTED", msg

        if threat:
            await self.handle_threat(ip, threat, details, parsed)

    async def on_ssh_line(self, line: str):
        parsed = LogParser.parse_ssh_line(line)
        if not parsed:
            return

        ip = parsed["ip"]
        if await self._should_skip(ip):
            return

        # Check for SSH Brute Force
        is_brute, msg = await SSHDetector.is_brute_force(ip, redis_client)
        if is_brute:
            # We'll use a dummy 'parsed' dictionary for handle_threat for SSH cases
            ssh_info = {
                "path": "SSH_AUTH",
                "user_agent": f"SSH User: {parsed['user']}"
            }
            await self.handle_threat(ip, "SSH BRUTE FORCE DETECTED", msg, ssh_info)

    async def _should_skip(self, ip):
        """Check if IP is already banned or whitelisted."""
        if await redis_client.is_ip_banned(ip):
            return True
        if await mysql_client.is_whitelisted(ip):
            return True
        return False

    async def handle_threat(self, ip, threat_type, details, parsed):
        print(f"[THREAT] {threat_type}: {ip} -> {details}")
        
        # Ban the IP
        await redis_client.ban_ip(ip)
        await firewall_mitigation.ban_ip(ip)
        
        # Log to Redis history
        history_item = f"[{time.ctime()}] {threat_type} from {ip}: {details} | Source: {parsed['path']}"
        await redis_client.add_to_list("attack_history", history_item)

        # Log to MySQL
        await mysql_client.log_attack(
            ip, threat_type, details, parsed['path'], parsed['user_agent']
        )
        
        # Send Telegram alert
        alert_msg = (
            f"Type: {threat_type}\n"
            f"IP: {ip}\n"
            f"Details: {details}\n"
            f"Context: {parsed['path']}\n"
            f"User-Agent/Info: {parsed['user_agent']}"
        )
        await telegram_alert_service.send_alert(threat_type, alert_msg)

if __name__ == "__main__":
    worker = MonitorWorker()
    asyncio.run(worker.run())
