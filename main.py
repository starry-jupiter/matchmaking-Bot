import threading
import asyncio
import os
from dashboard import app as flask_app
from app import bot
from dotenv import load_dotenv

load_dotenv()

def run_bot():
    # Flush=True forces the log to show up on Render immediately
    print("🟢 2. Starting Discord bot in background...", flush=True)
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("🔴 ERROR: DISCORD_TOKEN not found in environment variables!", flush=True)
        return

    # Discord requires its own event loop when running in a thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        print("🟢 3. Bot is attempting to log in...", flush=True)
        bot.run(token)
    except Exception as e:
        print(f"🔴 Discord Bot Crashed: {e}", flush=True)

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