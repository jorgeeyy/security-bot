import asyncio
import httpx
from config import settings
from .notifier import send

async def start(ban_ip, unban_ip, add_ignoreip, get_banned, get_status, whitelist):
    offset = 0
    # Create the AsyncClient. Adjust timeout since it performs long polling
    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            try:
                # Basic long polling using HTTP
                response = await client.get(
                    f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/getUpdates",
                    params={"offset": offset, "timeout": 30}
                )
                
                if response.status_code != 200:
                    await asyncio.sleep(5)
                    continue

                data = response.json()
                if not data.get("ok"):
                    await asyncio.sleep(5)
                    continue
                
                for item in data.get("result", []):
                    offset = item["update_id"] + 1
                    message = item.get("message", {})
                    text = message.get("text", "")
                    
                    if text.startswith("/"):
                        await handle_command(text, ban_ip, unban_ip, add_ignoreip, get_banned, get_status, whitelist)
            except Exception as e:
                print(f"[TG_POLL_ERR] {e}")
                await asyncio.sleep(5)

async def handle_command(text, ban_ip, unban_ip, add_ignoreip, get_banned, get_status, whitelist):
    parts = text.split()
    cmd = parts[0]
    args = parts[1:]
    
    try:
        if cmd == "/ban" and args:
            await ban_ip(args[0])
            await send(f"✅ Banned `{args[0]}`")
        elif cmd == "/unban" and args:
            await unban_ip(args[0])
            await send(f"✅ Unbanned `{args[0]}`")
        elif cmd == "/whitelist" and args:
            from store.whitelist import add_to_whitelist
            whitelist.clear()
            whitelist.update(add_to_whitelist(args[0]))
            await add_ignoreip(args[0]) # Prompt fail2ban configuration exception
            await send(f"✅ Whitelisted `{args[0]}`")
        elif cmd == "/banned":
            banned = await get_banned()
            await send(f"🔒 *Banned IPs*:\n```\n{banned}\n```")
        elif cmd == "/status":
            status = await get_status()
            await send(f"📊 *Status*:\n```\n{status}\n```")
        else:
            await send("❓ Unknown command or missing IP address.")
    except Exception as e:
        await send(f"❌ Error executing {cmd}: {e}")
