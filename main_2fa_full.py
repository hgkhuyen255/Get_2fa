from fastapi import FastAPI, Request
import os
import json
import pyotp
import httpx

app = FastAPI()

GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_API = f"https://api.github.com/gists/{GIST_ID}"

def load_secrets():
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        r = httpx.get(GIST_API, headers=headers).json()
        content = r["files"]["secrets.json"]["content"]
        return json.loads(content)
    except:
        return {}

def save_secrets(data):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {
        "files": {
            "secrets.json": {
                "content": json.dumps(data, indent=2)
            }
        }
    }
    httpx.patch(GIST_API, headers=headers, json=payload)

@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id or not text:
        return {"ok": True}

    def reply(msg):
        httpx.post(f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage", json={
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "HTML"
        })

    secrets = load_secrets()

    if text.startswith("/start"):
        reply("👋 Gửi email để nhận mã 2FA. Dùng /add, /edit, /delete.")
    elif text.startswith("/add"):
        lines = text.split("
")
        if len(lines) >= 2:
            email = lines[0].split(" ", 1)[-1].strip()
            secret = lines[1].strip()
            secrets[email] = secret
            save_secrets(secrets)
            reply(f"✅ Đã thêm {email}.")
        else:
            reply("⚠️ Sai cú pháp. Dùng /add email\nsecret")
    elif text.startswith("/edit"):
        lines = text.split("
")
        if len(lines) >= 2:
            email = lines[0].split(" ", 1)[-1].strip()
            secret = lines[1].strip()
            if email in secrets:
                secrets[email] = secret
                save_secrets(secrets)
                reply(f"✏️ Đã sửa {email}.")
            else:
                reply("❌ Không tìm thấy email trong hệ thống.")
        else:
            reply("⚠️ Sai cú pháp. Dùng /edit email\nsecret")
    elif text.startswith("/delete"):
        parts = text.split(" ", 1)
        if len(parts) == 2:
            email = parts[1].strip()
            if email in secrets:
                secrets.pop(email)
                save_secrets(secrets)
                reply(f"🗑️ Đã xoá {email}.")
            else:
                reply("❌ Không tìm thấy email trong hệ thống.")
        else:
            reply("⚠️ Sai cú pháp. Dùng /delete email")
    else:
        email = text.strip()
        if email in secrets:
            code = pyotp.TOTP(secrets[email]).now()
            reply(f"🔐 <b>{email}</b>: <code>{code}</code>")
        else:
            reply("❌ Không tìm thấy email trong hệ thống.")

    return {"ok": True}