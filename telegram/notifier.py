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
