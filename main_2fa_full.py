
import json
import os
import pyotp
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from github import Github

app = FastAPI()

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GIST_ID = os.environ.get("GIST_ID")
HEADERS = {"Accept": "application/vnd.github.v3+json"}
g = Github(GITHUB_TOKEN)
gist = g.get_gist(GIST_ID)

def load_data():
    file = gist.files["secrets.json"]
    return json.loads(file.content)

def save_data(data):
    gist.edit(files={"secrets.json": {"content": json.dumps(data)}})

@app.post("/")
async def telegram_webhook(req: Request):
    body = await req.json()
    message = body.get("message", {}).get("text", "")
    chat_id = body.get("message", {}).get("chat", {}).get("id")

    if not message or not chat_id:
        return JSONResponse(content={"ok": True})

    secrets = load_data()

    def reply(text):
        requests.post(
            f"https://api.telegram.org/bot{os.environ['BOT_TOKEN']}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        )

    if message.startswith("/start"):
        reply("👋 Gửi email để nhận mã 2FA. Dùng <code>/add</code>, <code>/edit</code>, <code>/delete</code>.")
    elif message.startswith("/add "):
        try:
            _, email, secret = message.split()
            secrets[email] = secret
            save_data(secrets)
            reply("✅ Đã thêm thành công.")
        except:
            reply("❌ Sai cú pháp. Dùng /add email secret")
    elif message.startswith("/edit "):
        try:
            _, email, secret = message.split()
            if email in secrets:
                secrets[email] = secret
                save_data(secrets)
                reply("✅ Đã sửa thành công.")
            else:
                reply("❌ Không tìm thấy email.")
        except:
            reply("❌ Sai cú pháp. Dùng /edit email secret")
    elif message.startswith("/delete "):
        email = message.replace("/delete ", "").strip()
        if email in secrets:
            secrets.pop(email)
            save_data(secrets)
            reply("✅ Đã xoá thành công.")
        else:
            reply("❌ Không tìm thấy email.")
    elif "@" in message:
        email = message.strip()
        secret = secrets.get(email)
        if secret:
            code = pyotp.TOTP(secret).now()
            reply(f"🔐 <b>{email}</b>
<code>{code}</code>")
        else:
            reply("❌ Không tìm thấy email trong hệ thống.")
    else:
        reply("❓ Không hiểu lệnh.")

    return JSONResponse(content={"ok": True})
