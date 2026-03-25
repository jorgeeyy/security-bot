from app.config import settings
from app.storage.redis_client import redis_client

class BotnetDetector:
    @staticmethod
    def get_subnet(ip: str):
        # Simply take the first 3 segments for /24 equivalent
        # e.g. 192.168.1.5 -> 192.168.1.*
        parts = ip.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.*"
        return None

    @staticmethod
    async def is_botnet_activity(ip, timestamp, r_client=redis_client):
        subnet = BotnetDetector.get_subnet(ip)
        if not subnet:
            return False, None
        
        # Track unique IPs per subnet in sliding window
        window_key = f"subnet_ips:{subnet}"
        # ZSET stores (IP, Time) to track active members in window
        # For unique IPs, we need something better.
        # Maybe a regular SET for IPs, and an expire? 
        # But we need a sliding window for counts.
        
        # We'll use a SET for each IP in the subnet that has hit us, 
        # and a general counter or sliding window per IP.
        # Simple implementation: 
        # 1. track each individual IP's frequency.
        # 2. Add the IP to a subnet-wide SET.
        
        await r_client.client.sadd(window_key, ip)
        await r_client.client.expire(window_key, settings.TIME_WINDOW)
        
        # Unique IPs in this subnet
        count = await r_client.client.scard(window_key)
        
        if count >= 10: # Threshold example: 10 IPs in subnet
            return True, f"Botnet activity: {count} unique IPs in subnet {subnet}"
        
        return False, None
