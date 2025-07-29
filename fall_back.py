import asyncio
import time
import requests
import threading
from datetime import datetime, timedelta
from flask import Flask, request
from telegram import Bot, Update
from telegram.constants import ParseMode

# === Configuration ===
BOT_TOKEN = '7794167983:AAFZwjzFVq-T4oljDLDAA-JTw9ywEp2Urb0'
CHECK_INTERVAL = 10        # seconds between ping checks
FALLBACK_TIMEOUT = 70    # 2 minutes = 120 seconds
MAINTENANCE_MSG = "<b>🚧 Bot is under maintenance</b>\nPlease wait a few minutes and try again.\n click on /about 👈🏻 to know how this bot work "
ABOUT_MSG = """<b>🚀 Promoter Bot shares your saved link with real users using smart automation, daily free boosts, and referrals.</b>

<a href="https://t.me/Testovila_bot">Track promotions</a> or track your link.

🛠️ The bot is currently under a little maintenance.

🎨 Visit our website to make your promotion message look attractive:
https://lnk.ink/Promostyle.com

🙏 Thank you for your patience!"""

JSONBIN_API_KEY = "$2a$10$x7VBgNRztww.OlDubg9dS.Q86N6zGeCi/6oSlWc3NE7wYYAW3deia"
JSONBIN_BIN_ID = "6888d942f7e7a370d1efd82c"
JSONBIN_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"
JSONBIN_HEADERS = {
    "X-Master-Key": JSONBIN_API_KEY,
    "Content-Type": "application/json"
}
# === Globals ===
app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
last_ping_time = datetime.min  # initialize to very old time
polling_active = False
stop_event = threading.Event()

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

def save_user_id_to_jsonbin(user_id: int):
    try:
        res = requests.get(JSONBIN_URL + '/latest', headers=JSONBIN_HEADERS)
        print("[JSONBin GET]", res.status_code)

        data = res.json().get('record', {}) if res.status_code == 200 else {}
        data[str(user_id)] = True

        time.sleep(1)  # avoid triggering rate limit

        response = requests.put(
            JSONBIN_URL,
            headers={**JSONBIN_HEADERS, "X-Bin-Versioning": "false"},
            json={"record": data}
        )
        print("[JSONBin PUT]", response.status_code, response.text)

    except Exception as e:
        print(f"[JSONBin] Save error: {e}")
        
# === Passive Polling Loop with Blink Logic ===
async def poll_updates_loop():
    global polling_active
    print("[Fallback] Telegram polling started.")
    offset = None

    try:
        while not stop_event.is_set():
            print("[Fallback] Polling ON (2s)...")
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < 1.2:
                try:
                    updates = await asyncio.wait_for(bot.get_updates(offset=offset, timeout=5), timeout=6)
                    if updates:
                        offset = updates[-1].update_id + 1
                        for update in updates:
                            if update.message and update.message.text:
                                try:
                                  save_user_id_to_jsonbin(update.effective_user.id)
                                except Exception as e:
                                  print(f"[User Save Error] {e}")
                                if update.message.text.strip() == "/about":
                                    await bot.send_message(
                                        chat_id=update.effective_chat.id,
                                        text=ABOUT_MSG,
                                        parse_mode=ParseMode.HTML
                                    )
                                else:
                                    await bot.send_message(
                                        chat_id=update.effective_chat.id,
                                        text=MAINTENANCE_MSG,
                                        parse_mode=ParseMode.HTML
                                    )
                except asyncio.TimeoutError:
                    pass  # No updates in this window
                except Exception as e:
                    print("Polling error:", e)
                if stop_event.is_set():
                    print("[Fallback] Stopping polling early due to ping.")
                    polling_active = False
                    return
            print("[Fallback] Polling OFF (3s)...")
            await asyncio.sleep(3)
    except Exception as e:
        print("[Fallback] Critical polling error:", e)
    finally:
        polling_active = False
        print("[Fallback] Polling loop exited.")

# === Watcher Thread to Control Polling ===
def fallback_watchdog():
    global polling_active
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while True:
        now = datetime.now()
        should_poll = (now - last_ping_time).total_seconds() > FALLBACK_TIMEOUT

        if should_poll and not polling_active:
            print("[Fallback] No ping received. Starting Telegram fallback mode...")
            stop_event.clear()
            loop.call_soon_threadsafe(loop.create_task, poll_updates_loop())
            polling_active = True
        elif not should_poll and polling_active:
            print("[Fallback] Ping received again. Stopping Telegram fallback mode.")
            stop_event.set()

        loop.run_until_complete(asyncio.sleep(CHECK_INTERVAL))

# === Start Everything ===
if __name__ == '__main__':
    threading.Thread(target=fallback_watchdog, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
    
