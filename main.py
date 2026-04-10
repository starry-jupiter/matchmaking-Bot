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
        print("🔴 ERROR: DISCORD_TOKEN not found in environment variables!", flush=True)
        return

    # The Relentless Retry Loop (Tries 5 times)
    for attempt in range(5):
        try:
            print(f"🟢 3. Bot is attempting to log in (Attempt {attempt + 1}/5)...", flush=True)
            
            # Setup the thread's event loop inside the retry so it's fresh every time
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # This will block and run forever if successful
            bot.run(token) 
            break # If the bot shuts down normally, break the loop
            
        except Exception as e:
            print(f"🔴 Discord connection failed: {e}", flush=True)
            if attempt < 4:
                print("⏳ Render network still waking up. Retrying in 10 seconds...", flush=True)
                time.sleep(10)
            else:
                print("🔴 Max retries reached. Bot failed to start.", flush=True)

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