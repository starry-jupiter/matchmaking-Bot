import threading
import asyncio
import os
import time
import sys

# 1. Force the Environment to load FIRST
from dotenv import load_dotenv
load_dotenv()

# 2. Import your logic
from dashboard import app as flask_app
from app import bot

def run_bot():
    print("🟢 2. Starting Discord bot in background...", flush=True)
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("🔴 ERROR: DISCORD_TOKEN not found!", flush=True)
        return

    print("⏳ Waiting 15 seconds for Render network...", flush=True)
    time.sleep(15) 

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        print("🟢 3. Bot is attempting to log in...", flush=True)
        bot.run(token)
    except Exception as e:
        print(f"🔴 Discord Bot Crashed: {e}", flush=True)
        os._exit(1)

# This is our "Safety Check" route
@flask_app.route('/health')
def health():
    return "Bot and Dashboard are Alive!", 200

if __name__ == "__main__":
    print("🟢 0. Main script starting!", flush=True)
    
    # --- ROUTE DEBUGGER ---
    # This will print EVERY route Flask knows about to your Render logs
    print("------------------------------------------")
    print("🔍 FLASK ROUTE CHECK:")
    for rule in flask_app.url_map.iter_rules():
        print(f"👉 Route found: {rule.endpoint} at {rule.rule}")
    print("------------------------------------------")

    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    print("🟢 1. Starting Flask server...", flush=True)
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)