import threading
import asyncio
import os
import time  # <--- 1. Import time at the top!
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

    # <--- 2. Add the 5-second Snooze Button here
    print("⏳ Waiting 5 seconds for Render network to connect...", flush=True)
    time.sleep(5) 

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        print("🟢 3. Bot is attempting to log in...", flush=True)
        bot.run(token)
    except Exception as e:
        print(f"🔴 Discord Bot Crashed: {e}", flush=True)

# ... (keep the rest of your health route and __main__ block exactly the same)