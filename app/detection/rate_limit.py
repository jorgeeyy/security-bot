from app.config import settings
from app.storage.redis_client import redis_client

class RateLimitDetector:
    RPS_THRESHOLD = 5
    
    @staticmethod
    async def is_rate_limited(ip, timestamp, r_client=redis_client):
        count = await r_client.record_request(ip, timestamp)
        
        if count >= RateLimitDetector.RPS_THRESHOLD:
            return True, f"Rate limit burst: {count} in {settings.TIME_WINDOW}s"
        
        return False, None
