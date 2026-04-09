import threading
import os
import time
from dashboard import app as flask_app
from app import bot
from dotenv import load_dotenv

load_dotenv()

@flask_app.route('/health')
def health():
    return "Bot and Dashboard are Alive!", 200

def run_flask():
    print("🟢 1. Starting Flask server...")
    port = int(os.environ.get("PORT", 10000))
    # use_reloader=False is CRITICAL when running Flask in a thread!
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    print("🟢 0. Main script starting!")
    
    # Start Flask in the background
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # Give the web server a 3-second head start to bind to Render's port
    time.sleep(3)
    
    # Now start the Discord Bot
    print("🟢 2. Starting Discord bot...")
    bot.run(os.getenv('DISCORD_TOKEN'))