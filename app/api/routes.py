from fastapi import APIRouter, HTTPException
from app.storage.redis_client import redis_client

router = APIRouter()

@router.get("/stats")
async def get_stats():
    """Returns general traffic stats (mocked for now)."""
    # In a real system, you'd increment stats in Redis for every request
    return {
        "status": "online",
        "monitoring": True,
        "active_bans": await redis_client.client.keys("banned:*")
    }

@router.get("/attacks")
async def get_attacks(limit: int = 10):
    """Returns recent threats/attacks."""
    history = await redis_client.get_list("attack_history", 0, limit - 1)
    return {"recent_attacks": history}

@router.get("/banned-ips")
async def get_banned_ips():
    """Returns a list of currently blocked IPs."""
    keys = await redis_client.client.keys("banned:*")
    ips = [key.replace("banned:", "") for key in keys]
    return {"banned_ips": ips}

@router.post("/unban/{ip}")
async def unban_ip(ip: str):
    """Manually unban an IP."""
    await redis_client.client.delete(f"banned:{ip}")
    return {"message": f"IP {ip} unbanned"}

@router.post("/whitelist/{ip}")
async def whitelist_ip(ip: str):
    """Manually whitelist an IP in MySQL."""
    from app.storage.mysql_client import mysql_client
    await mysql_client.add_to_whitelist(ip, "Manual via API")
    return {"message": f"IP {ip} added to whitelist"}
