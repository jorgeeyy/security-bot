import aiomysql
from app.config import settings

class MySQLClient:
    def __init__(self):
        self.pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await aiomysql.create_pool(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                db=settings.MYSQL_DB,
                autocommit=True
            )

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def log_attack(self, ip, threat_type, details, path, user_agent):
        """Save an attack event to the MySQL database."""
        if not self.pool:
            try:
                await self.connect()
            except Exception as e:
                print(f"[MYSQL_ERR] Failed connect during log: {e}")
                return

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                sql = """
                INSERT INTO attacks (ip, threat_type, details, path, user_agent) 
                VALUES (%s, %s, %s, %s, %s)
                """
                try:
                    await cur.execute(sql, (ip, threat_type, details, path, user_agent))
                except Exception as e:
                    print(f"[MYSQL_ERR] Failed to log attack: {e}")

    async def is_whitelisted(self, ip):
        """Check if an IP is whitelisted."""
        if not self.pool:
            try:
                await self.connect()
            except Exception:
                return False

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT ip FROM whitelist WHERE ip = %s", (ip,))
                return await cur.fetchone() is not None

    async def add_to_whitelist(self, ip, reason="Manual"):
        """Add an IP to the whitelist."""
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT IGNORE INTO whitelist (ip, reason) VALUES (%s, %s)",
                    (ip, reason)
                )

mysql_client = MySQLClient()
