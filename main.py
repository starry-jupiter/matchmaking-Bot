import threading
import os
from flask import Flask
from dashboard import admin_bp  # Matches your new filename dashboard.py
from app import bot             # Matches your bot instance in app.py
from dotenv import load_dotenv

load_dotenv()

# 1. Initialize the Flask App
app = Flask(__name__)

# 2. Register the Blueprint from dashboard.py
app.register_blueprint(admin_bp)

# 3. Health check for Render/UptimeRobot
@app.route('/health')
def health():
    return "Bot and Dashboard are Alive!", 200

def run_flask():
    # Render uses the PORT environment variable (default 10000)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Start Flask in the background
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # Start the Discord Bot in the foreground
    # This keeps the script running
    bot.run(os.getenv('DISCORD_TOKEN'))