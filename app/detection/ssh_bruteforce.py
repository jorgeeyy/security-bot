from app.config import settings

class SSHDetector:
    @staticmethod
    async def is_brute_force(ip, redis_client):
        """Check if an IP is brute-forcing SSH using Redis counters."""
        key = f"ssh:fails:{ip}"
        # Increment the failure counter for this IP
        count = await redis_client.client.incr(key)
        
        # Set expiry on first failure
        if count == 1:
            await redis_client.client.expire(key, settings.SSH_TIME_WINDOW)
        
        if count >= settings.SSH_MAX_ATTEMPTS:
            return True, f"SSH Brute Force: {count} failed attempts in {settings.SSH_TIME_WINDOW}s"
        
        return False, None
