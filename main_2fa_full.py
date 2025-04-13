
import os
import json
import requests
import pyotp
from fastapi import FastAPI, Request

app = FastAPI()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_ID = os.getenv("GIST_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")

def get_secrets():
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    data = res.json()
    content = data["files"]["secrets.json"]["content"]
    return json.loads(content)

def update_secrets(data):
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    update = {"files": {"secrets.json": {"content": json.dumps(data, indent=2)}}}
    requests.patch(url, headers=headers, json=update)

def reply(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)

@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    msg = data.get("message")
    if not msg:
        return {"ok": True}
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()
    secrets = get_secrets()

    if text.startswith("/start"):
        reply(chat_id, "👋 Gửi email để nhận mã 2FA. Dùng /add, /edit, /delete.")
    elif text.startswith("/add") or text.startswith("/edit"):
        lines = text.split("\n")
        if len(lines) >= 2:
            email = lines[0].split(maxsplit=1)[-1].strip()
            secret = lines[1].strip()
            secrets[email] = secret
            update_secrets(secrets)
            reply(chat_id, f"✅ Đã lưu <b>{email}</b>")
        else:
            reply(chat_id, "❌ Sai cú pháp. Gửi:\n<code>/add email\nsecret</code>")
    elif text.startswith("/delete"):
        email = text.split(maxsplit=1)[-1].strip()
        if email in secrets:
            del secrets[email]
            update_secrets(secrets)
            reply(chat_id, f"🗑️ Đã xóa <b>{email}</b>")
        else:
            reply(chat_id, "❌ Không tìm thấy email để xóa.")
    elif "@" in text:
        email = text.strip()
        if email in secrets:
            code = pyotp.TOTP(secrets[email]).now()
            reply(chat_id, f"🔐 <b>{email}</b>: <code>{code}</code>")
        else:
            reply(chat_id, "❌ Không tìm thấy email trong hệ thống.")
    else:
        reply(chat_id, "🤖 Không hiểu yêu cầu. Gửi /start để bắt đầu.")

@app.get("/")
def root():
    return {"status": "ok"}
