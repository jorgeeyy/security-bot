import httpx
import html
from app.config import settings

class TelegramAlertService:
    def __init__(self, bot_token=settings.TELEGRAM_BOT_TOKEN, chat_id=settings.TELEGRAM_CHAT_ID):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    async def send_alert(self, title: str, details: str):
        """Send a formatted telegram alert message."""
        if not self.bot_token or not self.chat_id:
            # Silently log if not configured
            print(f"[TELEGRAM_ALERT] Not configured. Would send: {title} - {details}")
            return
        
        # Escape for HTML parse mode
        safe_title = html.escape(title)
        safe_details = html.escape(details)
        message = f"🚨 <b>{safe_title}</b>\n\n{safe_details}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                })
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"[TELEGRAM_ERR] FAILED to send alert: {e}")
            return None

telegram_alert_service = TelegramAlertService()
