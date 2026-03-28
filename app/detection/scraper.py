class ScraperDetector:
    SENSITIVE_PATHS = [
        ".env",
        ".git",
        "/admin",
        "/wp-admin",
        "/phpmyadmin",
        ".bak",
        ".config",
        "/.ssh",
        "/docker-compose.yml",
        "/etc/passwd"
    ]

    @staticmethod
    def is_scraper(path: str):
        path_lower = path.lower()
        for sensitive in ScraperDetector.SENSITIVE_PATHS:
            if sensitive in path_lower:
                return True, f"Sensitive path access: {sensitive}"
        
        return False, None
    
    @staticmethod
    async def check_path_diversity(ip, path, redis_client):
        """Check path diversity for a single IP (too many unique paths)."""
        diversity_key = f"paths_visited:{ip}"
        
        count_before = await redis_client.client.scard(diversity_key)
        await redis_client.client.sadd(diversity_key, path)
        
        if count_before == 0:
            await redis_client.client.expire(diversity_key, 3600)  # expires in 1 hour
            
        new_count = await redis_client.client.scard(diversity_key)
        
        if new_count > 50:  # Threshold for page diversity
            return True, f"High path diversity: {new_count} paths"
        return False, None
