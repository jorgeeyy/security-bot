import asyncio
import subprocess
from app.config import settings

class FirewallMitigation:
    @staticmethod
    async def ban_ip(ip: str, duration: int = settings.BAN_TIME):
        """Ban an IP using iptables or ufw."""
        if not settings.BAN_ENABLED:
            print(f"[MITIGATION] Ban disabled. Would ban: {ip}")
            return
            
        print(f"[MITIGATION] Banning IP: {ip} for {duration} seconds.")
        
        # iptables command: iptables -A INPUT -s IP -j DROP
        # or ufw: ufw deny from IP
        # We'll use iptables for raw control
        try:
            # Add rule
            process = await asyncio.create_subprocess_exec(
                "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                print(f"[MITIGATION_ERR] Failed to ban IP via iptables: {stderr.decode()}")
            else:
                # Schedule unban
                asyncio.create_task(FirewallMitigation.unban_ip_after(ip, duration))
        except FileNotFoundError:
            print("[MITIGATION_ERR] iptables command not found (perhaps in Docker or local Windows?). Mocking ban.")

    @staticmethod
    async def unban_ip_after(ip: str, duration: int):
        await asyncio.sleep(duration)
        print(f"[MITIGATION] Unbanning IP: {ip}")
        try:
            process = await asyncio.create_subprocess_exec(
                "iptables", "-D", "INPUT", "-s", ip, "-j", "DROP",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            await process.communicate()
        except FileNotFoundError:
            pass

firewall_mitigation = FirewallMitigation()
