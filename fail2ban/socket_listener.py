import asyncio
import json
import os

SOCKET_PATH = "/run/monitor-bot/bot.sock"

async def start(on_event):
    # Only establish the socket loop if this is running on an active Linux system, 
    # skip if run natively on Windows during testing
    if os.name == 'nt':
        print("[WARN] Skipping Unix Socket Listener on Windows environment.")
        return
        
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
