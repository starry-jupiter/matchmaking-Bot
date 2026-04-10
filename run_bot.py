import os
import threading
from flask import Flask
from dotenv import load_dotenv
from app import bot

load_dotenv()

# Render Free Tier Bypass: A tiny invisible web server so Render doesn't crash the bot
health_app = Flask(__name__)

@health_app.route('/')
def health():
    return "Bot is awake and running!", 200

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    health_app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    
    # Start the invisible web server in the background
    print("🟢 Spinning up dummy health server for Render...")
    threading.Thread(target=keep_alive, daemon=True).start()
    
    # Start the actual Discord Bot
    print("🏹 Cupid Bot is taking flight...")
    bot.run(token)