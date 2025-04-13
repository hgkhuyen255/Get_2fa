import json
import os
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

DATA_FILE = "secrets.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def reply(chat_id, text, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    })

@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not chat_id or not text:
        return {"ok": True}

    if text.startswith("/start"):
        reply(chat_id, "👋 Gửi email để nhận mã 2FA. Dùng <code>/add</code>, <code>/edit</code>, <code>/delete</code>.")
    elif text.startswith("/add "):
        lines = text.split("
")
        if len(lines) >= 2:
            email = lines[0].replace("/add", "").strip()
            secret = lines[1].strip()
            data = load_data()
            data[email] = secret
            save_data(data)
            reply(chat_id, f"✅ Đã lưu <b>{email}</b>.")
        else:
            reply(chat_id, "❌ Sai cú pháp. Gửi:
<code>/add email@example.com</code>
<code>SECRETKEY</code>")
    elif text.startswith("/delete "):
        email = text.replace("/delete", "").strip()
        data = load_data()
        if email in data:
            del data[email]
            save_data(data)
            reply(chat_id, f"🗑️ Đã xoá <b>{email}</b>.")
        else:
            reply(chat_id, "❌ Không tìm thấy email trong hệ thống.")
    elif text.startswith("/edit "):
        lines = text.split("
")
        if len(lines) >= 2:
            email = lines[0].replace("/edit", "").strip()
            secret = lines[1].strip()
            data = load_data()
            if email in data:
                data[email] = secret
                save_data(data)
                reply(chat_id, f"✏️ Đã cập nhật <b>{email}</b>.")
            else:
                reply(chat_id, "❌ Không tìm thấy email trong hệ thống.")
        else:
            reply(chat_id, "❌ Sai cú pháp. Gửi:
<code>/edit email@example.com</code>
<code>NEWSECRETKEY</code>")
    else:
        email = text.strip()
        data = load_data()
        if email in data:
            reply(chat_id, f"🔐 <b>{email}</b>:
<code>{data[email]}</code>")
        else:
            reply(chat_id, "❌ Không tìm thấy email trong hệ thống.")

    return {"ok": True}