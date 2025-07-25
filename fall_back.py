import asyncio
import threading
from datetime import datetime, timedelta
from flask import Flask, request
from telegram import Bot, Update
from telegram.constants import ParseMode

# === Configuration ===
BOT_TOKEN = '7786407965:AAHlLwNr8x_Q-2SFhHoTKaPSth9hQgdJ6rM'
CHECK_INTERVAL = 5        # seconds between polling attempts
FALLBACK_TIMEOUT = 180    # 3 minutes = 180 seconds
MAINTENANCE_MSG = "<b>🚧 Bot is under maintenance</b>\nPlease wait a few minutes and try again."
ABOUT_MSG = "<b>This bot is temporarily under maintenance.</b>\n\nPlease wait while we restore full service. Thank you for your patience 🙏"

# === Globals ===
app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
last_ping_time = datetime.min  # initialize to very old time

# === Flask Routes ===
@app.route('/ping', methods=['POST'])
def ping():
    global last_ping_time
    last_ping_time = datetime.now()
    return "Ping received ✅", 200

@app.route('/health')
def health():
    return "Fallback bot alive ✅", 200

@app.route('/about')
def about():
    return ABOUT_MSG, 200

# === Passive Polling Loop ===
async def poll_updates():
    print("[Fallback] Passive update loop started.")
    offset = None
    while True:
        try:
            updates = await bot.get_updates(offset=offset, timeout=30)
            if updates:
                offset = updates[-1].update_id + 1
                now = datetime.now()
                fallback_active = (now - last_ping_time).total_seconds() > FALLBACK_TIMEOUT
                for update in updates:
                    if update.message and update.message.text:
                        if update.message.text.strip() == "/about":
                            await bot.send_message(
                                chat_id=update.effective_chat.id,
                                text=ABOUT_MSG,
                                parse_mode=ParseMode.HTML
                            )
                        elif fallback_active:
                            await bot.send_message(
                                chat_id=update.effective_chat.id,
                                text=MAINTENANCE_MSG,
                                parse_mode=ParseMode.HTML
                            )
        except Exception as e:
            print("Error in polling:", e)
        await asyncio.sleep(CHECK_INTERVAL)

# === Thread Wrapper ===
def start_telegram():
    asyncio.run(poll_updates())

# === Start Everything ===
if __name__ == '__main__':
    threading.Thread(target=start_telegram, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
