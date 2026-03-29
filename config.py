import os

class Settings:
    TELEGRAM_TOKEN : str = os.getenv("TELEGRAM_BOT_TOKEN", "your-token-here")
    CHAT_ID        : str = os.getenv("TELEGRAM_CHAT_ID", "your-chat-id-here")
    NGINX_LOG_PATH : str = os.getenv("NGINX_LOG_PATH", "/var/log/nginx/access.log")
    SOCKET_PATH    : str = "/run/monitor-bot/bot.sock"
    WHITELIST_PATH : str = "/opt/monitor-bot/whitelist.txt"

settings = Settings()
