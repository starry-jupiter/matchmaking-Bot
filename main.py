import threading
import asyncio
import os
from dashboard import app as flask_app
from app import bot
from dotenv import load_dotenv

load_dotenv()

def run_bot():
    print("🟢 2. Starting Discord bot in background...")
    # Discord requires its own event loop when running in a thread!
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        bot.run(os.getenv('DISCORD_TOKEN'))
    except Exception as e:
        print(f"🔴 Discord Bot Crashed: {e}")

@flask_app.route('/health')
def health():
    return "Bot and Dashboard are Alive!", 200

if __name__ == "__main__":
    print("🟢 0. Main script starting!")
    
    # Start Discord in the background thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Run Flask in the MAIN thread so Render is always happy
    print("🟢 1. Starting Flask server on main thread...")
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)