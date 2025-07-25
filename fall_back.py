import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from datetime import datetime, timedelta
import threading

# === CONFIG ===
BOT_TOKEN = "YOUR_FALLBACK_BOT_TOKEN"
PING_TIMEOUT = 180  # 3 minutes
app = Flask(__name__)
last_ping = datetime.utcnow()

# === /ping from main bot ===
@app.route("/ping", methods=["POST"])
def ping():
    global last_ping
    last_ping = datetime.utcnow()
    return "✅ Ping received", 200

# === UptimeRobot health check ===
@app.route("/health")
def health():
    return "✅ Fallback bot is running", 200

# === Telegram command: /about ===
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = """🤖 <b>Bot Under Maintenance</b>

This is the fallback responder for the Link Promotion Bot.

🛠️ The main bot is currently <b>offline or restarting</b>.
Please wait a few minutes and try again.

If this message keeps appearing, contact the bot admin or owner.

💬 Thank you for your patience!
"""
    await update.message.reply_text(message, parse_mode=ParseMode.HTML)

# === Reply to all messages when main bot is down ===
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    delta = datetime.utcnow() - last_ping
    if delta.total_seconds() > PING_TIMEOUT:
        await update.message.reply_text(
            "🚧 Bot is currently under maintenance. Please try again later.",
            parse_mode=ParseMode.HTML
        )

# === Start the Telegram bot ===
def start_telegram():
    app_telegram = Application.builder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("about", about))
    app_telegram.add_handler(MessageHandler(filters.ALL, handle_all))
    app_telegram.run_polling()

# === Start both Flask and Telegram ===
if __name__ == "__main__":
    threading.Thread(target=start_telegram, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
