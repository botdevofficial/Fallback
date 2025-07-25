import asyncio
from flask import Flask, request
from telegram import Bot, Update
from telegram.constants import ParseMode
import threading
from datetime import datetime, timedelta

# === Configuration ===
BOT_TOKEN = "YOUR_FALLBACK_BOT_TOKEN"
PING_TIMEOUT = 180  # 3 minutes

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)
last_ping = datetime.utcnow()

# === /health for UptimeRobot ===
@app.route("/health")
def health():
    return "✅ Fallback bot is alive", 200

# === /ping from main bot ===
@app.route("/ping", methods=["POST"])
def ping():
    global last_ping
    last_ping = datetime.utcnow()
    return "✅ Ping received", 200

# === Handle incoming updates manually ===
async def handle_update(update: Update):
    global last_ping
    delta = datetime.utcnow() - last_ping

    if update.message:
        text = update.message.text or ""

        if text.startswith("/about"):
            await bot.send_message(
                chat_id=update.message.chat_id,
                text=(
                    "🤖 <b>This is the fallback responder bot.</b>\n\n"
                    "🛠️ The main bot is currently <b>offline or restarting</b>.\n"
                    "Please wait a few minutes and try again later.\n\n"
                    "Thank you for your patience!",
                ),
                parse_mode=ParseMode.HTML
            )

        elif delta.total_seconds() > PING_TIMEOUT:
            await bot.send_message(
                chat_id=update.message.chat_id,
                text="🚧 Bot is currently under maintenance. Please try again later.",
                parse_mode=ParseMode.HTML
            )

# === Polling for new messages (manual async loop) ===
async def poll_updates():
    offset = None
    while True:
        try:
            updates = await bot.get_updates(offset=offset, timeout=30)
            for update in updates:
                offset = update.update_id + 1
                await handle_update(update)
        except Exception as e:
            print("Polling error:", e)
        await asyncio.sleep(1)

# === Start async loop ===
def start_async_loop():
    asyncio.run(poll_updates())

# === Main startup ===
if __name__ == '__main__':
    threading.Thread(target=start_async_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
