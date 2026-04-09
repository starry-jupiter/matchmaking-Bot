import threading
import os
from flask import Flask
from app import bot  # Import the bot instance from your app.py
from admin import app as flask_app # Import your Flask app from admin.py

# 1. Setup a simple health check for UptimeRobot
@flask_app.route('/health')
def health():
    return "Bot is Alive!", 200

def run_flask():
    # Render provides a dynamic PORT variable; default to 10000
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # 2. Start Flask in a separate thread (Background)
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # 3. Start the Discord Bot (Foreground)
    bot.run(os.getenv('DISCORD_TOKEN'))