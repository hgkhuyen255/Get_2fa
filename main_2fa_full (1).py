
import json
import os
from fastapi import FastAPI, Request
import pyotp
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.ext import CallbackContext
import asyncio

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

app = FastAPI()

secrets = {}

def load_secrets():
    global secrets
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        url = f"https://api.github.com/gists/{GIST_ID}"
        response = httpx.get(url, headers=headers)
        if response.status_code == 200:
            secrets = json.loads(response.json()["files"]["secrets.json"]["content"])
        else:
            secrets = {}
    except:
        secrets = {}

def save_secrets():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    url = f"https://api.github.com/gists/{GIST_ID}"
    payload = {
        "files": {
            "secrets.json": {
                "content": json.dumps(secrets, indent=2)
            }
        }
    }
    httpx.patch(url, headers=headers, json=payload)

@app.on_event("startup")
async def startup_event():
    load_secrets()
    app.bot_app = Application.builder().token(BOT_TOKEN).build()
    app.bot_app.add_handler(CommandHandler("start", start))
    app.bot_app.add_handler(CommandHandler("add", add_secret))
    app.bot_app.add_handler(CommandHandler("edit", edit_secret))
    app.bot_app.add_handler(CommandHandler("delete", delete_secret))
    asyncio.create_task(app.bot_app.initialize())
    await app.bot_app.bot.set_webhook(WEBHOOK_URL + "/webhook")
    asyncio.create_task(app.bot_app.start())

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    await app.bot_app.process_update(Update.de_json(data, app.bot_app.bot))
    return {"ok": True}

async def start(update: Update, context: CallbackContext.DEFAULT_TYPE):
    await update.message.reply_text("👋 Gửi email để nhận mã 2FA. Dùng /add, /edit, /delete.")

async def add_secret(update: Update, context: CallbackContext.DEFAULT_TYPE):
    text = update.message.text
    lines = text.split("\n")
    if len(lines) < 2:
        await update.message.reply_text(
            "❌ Định dạng sai. Gửi:\n<code>/add email@example.com\\nSECRET</code>",
            parse_mode="HTML"
        )
<code>/add email@example.com\nSECRET</code>", parse_mode="HTML")
        return
    email = lines[0].replace("/add", "").strip()
    secret = lines[1].strip()
    secrets[email] = secret
    save_secrets()
    await update.message.reply_text("👍 Đã thêm.")

async def edit_secret(update: Update, context: CallbackContext.DEFAULT_TYPE):
    text = update.message.text
    lines = text.split("\n")
    if len(lines) < 2:
        await update.message.reply_text("❌ Định dạng sai. Gửi:
<code>/edit email@example.com\nSECRET_MOI</code>", parse_mode="HTML")
        return
    email = lines[0].replace("/edit", "").strip()
    if email not in secrets:
        await update.message.reply_text("❌ Email chưa có trong hệ thống.")
        return
    secret = lines[1].strip()
    secrets[email] = secret
    save_secrets()
    await update.message.reply_text("✏️ Đã cập nhật.")

async def delete_secret(update: Update, context: CallbackContext.DEFAULT_TYPE):
    email = update.message.text.replace("/delete", "").strip()
    if email not in secrets:
        await update.message.reply_text("❌ Email chưa có.")
        return
    del secrets[email]
    save_secrets()
    await update.message.reply_text("🗑️ Đã xóa.")

@app.get("/")
async def root():
    return {"message": "Bot 2FA is running"}
