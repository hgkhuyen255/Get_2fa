import os
import json
import pyotp
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET_PATH = "/webhook"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_ID = os.getenv("GIST_ID")

app = FastAPI()
secrets = {}

def load_secrets():
    global secrets
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
    data = r.json()
    secrets = json.loads(data["files"]["secrets.json"]["content"])

def save_secrets():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "files": {
            "secrets.json": {
                "content": json.dumps(secrets, indent=2)
            }
        }
    }
    requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=headers, json=payload)

def get_2fa(secret):
    return pyotp.TOTP(secret).now()

@app.on_event("startup")
def startup_event():
    load_secrets()

@app.post(WEBHOOK_SECRET_PATH)
async def telegram_webhook(req: Request):
    data = await req.json()
    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        def reply(message):
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            })

        lines = text.strip().split("\n")
        if lines[0].lower().startswith("/add") and len(lines) == 2:
            name = lines[0][4:].strip()
            secret = lines[1].strip()
            if name and secret:
                secrets[name] = secret
                save_secrets()
                reply("✅ Thêm thành công")
            else:
                reply("❌ Sai cú pháp. Gửi:\n/add tên\nSECRET")
        elif lines[0].lower().startswith("/delete"):
            name = lines[0][7:].strip()
            if name in secrets:
                secrets.pop(name)
                save_secrets()
                reply("🗑️ Đã xoá")
            else:
                reply("❌ Không tìm thấy")
        elif lines[0].lower().startswith("/edit") and len(lines) == 2:
            name = lines[0][5:].strip()
            secret = lines[1].strip()
            if name in secrets:
                secrets[name] = secret
                save_secrets()
                reply("✏️ Đã cập nhật")
            else:
                reply("❌ Không tìm thấy để sửa")
        elif text.lower().startswith("/start"):
            reply("👋 Gửi tên để nhận mã 2FA.\nDùng /add, /edit, /delete.")
        else:
            name = text.strip()
            if name in secrets:
                reply(f"⏰ Mã 2FA: <b>{get_2fa(secrets[name])}</b>")
            else:
                reply("❌ Không tìm thấy tên trong hệ thống.")

    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
def root():
    return "<h1>Get 2FA Bot đang chạy.</h1>"
