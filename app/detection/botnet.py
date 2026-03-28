from app.config import settings
from app.storage.redis_client import redis_client

class BotnetDetector:
    @staticmethod
    def get_subnet(ip: str):
        # Handle IPv4
        parts = ip.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.*"
        # Handle IPv6 (group by first 3 blocks)
        v6_parts = ip.split(':')
        if len(v6_parts) >= 3:
            return f"{v6_parts[0]}:{v6_parts[1]}:{v6_parts[2]}:*"
        return None

    @staticmethod
    async def is_botnet_activity(ip, timestamp, r_client=redis_client):
        subnet = BotnetDetector.get_subnet(ip)
        if not subnet:
            return False, None
        
        window_key = f"subnet_ips:{subnet}"
        
        count_before = await r_client.client.scard(window_key)
        await r_client.client.sadd(window_key, ip)
        
        # Set expire only if it's the first IP in the subnet block to avoid infinite TTL extensions
        if count_before == 0:
            await r_client.client.expire(window_key, settings.TIME_WINDOW)
        
        # Unique IPs in this subnet
        count = await r_client.client.scard(window_key)
        
        if count >= 10: # Threshold example: 10 IPs in subnet
            return True, f"Botnet activity: {count} unique IPs in subnet {subnet}"
        
        return False, None
