import json
import os
import requests
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import pyotp

app = FastAPI()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_ID = os.getenv("GIST_ID")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

secrets_cache = {}

def load_secrets():
    global secrets_cache
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        r = requests.get(url, headers=HEADERS)
        files = r.json().get("files", {})
        content = files.get("secrets.json", {}).get("content", "{}")
        secrets_cache = json.loads(content)
        print("🔄 Secrets loaded from Gist.")
    except Exception as e:
        print("⚠️ Failed to load secrets:", e)
        secrets_cache = {}

def save_secrets():
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        data = {
            "files": {
                "secrets.json": {
                    "content": json.dumps(secrets_cache, indent=4)
                }
            }
        }
        response = requests.patch(url, headers=HEADERS, json=data)
        print("💾 Gist save:", response.status_code, response.text)
        return response.ok
    except Exception as e:
        print("⚠️ Failed to save secrets:", e)
        return False

@app.on_event("startup")
async def startup_event():
    load_secrets()

@app.post("/webhook")
async def handle_message(request: Request):
    body = await request.json()
    message = body.get("message", {}).get("text", "")
    chat_id = body.get("message", {}).get("chat", {}).get("id", "")

    reply = "Xin chào"
    parts = message.strip().split()

    if len(parts) >= 1:
        command = parts[0].lower()

        if command == "add" and len(parts) == 3:
            name, secret = parts[1], parts[2]
            secrets_cache[name] = secret
            save_secrets()
            reply = f"✅ Đã thêm {name}"

        elif command == "edit" and len(parts) == 3:
            name, secret = parts[1], parts[2]
            if name in secrets_cache:
                secrets_cache[name] = secret
                save_secrets()
                reply = f"✏️ Đã sửa {name}"
            else:
                reply = "❌ Không tồn tại"

        elif command == "delete" and len(parts) == 2:
            name = parts[1]
            if name in secrets_cache:
                del secrets_cache[name]
                save_secrets()
                reply = f"🗑️ Đã xoá {name}"
            else:
                reply = "❌ Không tồn tại"

        elif message.strip() in secrets_cache:
            name = message.strip()
            totp = pyotp.TOTP(secrets_cache[name])
            reply = f"⏱ Mã 2FA: {totp.now()}"

    token = os.getenv("BOT_TOKEN")
    telegram_url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(telegram_url, json={"chat_id": chat_id, "text": reply})

    return PlainTextResponse("OK")