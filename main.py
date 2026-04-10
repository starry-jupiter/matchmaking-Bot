import threading
import asyncio
import os
import time
from dashboard import app as flask_app
from app import bot
from dotenv import load_dotenv

load_dotenv()

def run_bot():
    print("🟢 2. Starting Discord bot in background...", flush=True)
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("🔴 ERROR: DISCORD_TOKEN not found!", flush=True)
        return

    # Give Render a generous 15 seconds to wake up its DNS
    print("⏳ Waiting 15 seconds for Render network to connect...", flush=True)
    time.sleep(15) 

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        print("🟢 3. Bot is attempting to log in...", flush=True)
        bot.run(token)
    except Exception as e:
        print(f"🔴 Discord Bot Crashed: {e}", flush=True)
        print("🔄 Forcing Render to restart the container for a fresh network...", flush=True)
        os._exit(1) # This forces the entire app to reboot!

@flask_app.route('/health')
def health():
    return "Bot and Dashboard are Alive!", 200

if __name__ == "__main__":
    print("🟢 0. Main script starting!", flush=True)
    
    # Start Discord in the background thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Run Flask in the MAIN thread
    print("🟢 1. Starting Flask server on main thread...", flush=True)
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)