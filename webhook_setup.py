import os
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
RAILWAY_URL = os.getenv("RAILWAY_URL")  # Domain Railway ví dụ: https://your-bot.up.railway.app/

def set_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    webhook_url = f"{RAILWAY_URL}/"
    response = requests.get(url, params={"url": webhook_url})
    print("Webhook response:", response.json())

if __name__ == "__main__":
    set_webhook()
