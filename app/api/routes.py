from fastapi import APIRouter, HTTPException
from app.storage.redis_client import redis_client

router = APIRouter()

@router.get("/stats")
async def get_stats():
    """Returns real-time traffic and threat stats."""
    total_reqs = await redis_client.client.get("stats:total_requests") or 0
    total_blocks = await redis_client.client.get("stats:total_blocks") or 0
    active_bans = await redis_client.client.keys("banned:*")
    
    return {
        "status": "online",
        "monitoring": True,
        "total_requests_processed": int(total_reqs),
        "total_threats_blocked": int(total_blocks),
        "currently_banned_count": len(active_bans)
    }

@router.get("/attacks")
async def get_attacks(limit: int = 10):
    """Returns recent threats/attacks."""
    history = await redis_client.get_list("attack_history", 0, limit - 1)
    return {"recent_attacks": history}

@router.get("/banned-ips")
async def get_banned_ips():
    """List all currently banned IPs in Redis."""
    keys = await redis_client.client.keys("banned:*")
    return {"banned_ips": [k.replace("banned:", "") for k in keys]}

@router.get("/whitelist")
async def get_whitelist():
    """List all whitelisted IPs in MySQL."""
    from app.storage.mysql_client import mysql_client
    return {"whitelist": await mysql_client.get_all_whitelisted()}

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

@router.delete("/whitelist/{ip}")
async def remove_whitelist_ip(ip: str):
    """Manually remove an IP from the MySQL whitelist."""
    from app.storage.mysql_client import mysql_client
    await mysql_client.remove_from_whitelist(ip)
    return {"message": f"IP {ip} removed from whitelist"}
