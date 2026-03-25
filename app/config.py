import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = "your_bot_token"
    TELEGRAM_CHAT_ID: str = "your_chat_id"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    MOCK_MODE: bool = True  # Set to True for local testing without Redis/iptables

    # We use a default that depends on MOCK_MODE, but this will be overridden by .env
    NGINX_LOG_PATH: str = "/var/log/nginx/access.log"

    BOTNET_THRESHOLD: int = 20
    TIME_WINDOW: int = 30  # seconds

    BAN_ENABLED: bool = True
    BAN_TIME: int = 600  # seconds (10 mins)

    # Database
    MYSQL_HOST: str = "localhost"
    MYSQL_USER: str = "security_user"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DB: str = "security_bot"
    MYSQL_PORT: int = 3306

    POSTGRES_DSN: str = "postgresql://user:password@localhost:5432/security_bot"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Post-Init check for Mock Mode defaults
if settings.MOCK_MODE and settings.NGINX_LOG_PATH == "/var/log/nginx/access.log":
    settings.NGINX_LOG_PATH = "./test_access.log"
