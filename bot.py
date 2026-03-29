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
        await ban_ip(ip, jail="nginx-botsearch")
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
