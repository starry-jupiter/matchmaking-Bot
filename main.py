import threading
import os
from dashboard import app as flask_app  # <--- FIX: Import the configured app
from app import bot                     # Import the bot
from dotenv import load_dotenv

load_dotenv()

# Health check for Render
@flask_app.route('/health')
def health():
    return "Bot and Dashboard are Alive!", 200

def run_flask():
    # Render uses port 10000 by default
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Start Flask in the background
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # Start the Discord Bot in the foreground
    bot.run(os.getenv('DISCORD_TOKEN'))