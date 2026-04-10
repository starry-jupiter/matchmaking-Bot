import threading
import asyncio
import os
import time
import requests
from flask import Flask, render_template_string, redirect, request, session, url_for
from admin import admin_bp
from app import bot
import database

# 1. Initialize Environment
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
# Using your tech-chic signature for the secret key! 
app.secret_key = os.getenv("FLASK_SECRET_KEY", "madison-vennie-tech-chic-2026")
app.register_blueprint(admin_bp)

# --- DISCORD SETTINGS ---
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
OAUTH_URL = os.getenv("OAUTH_URL")
API_BASE = "https://discord.com/api/v10"

# --- IMPORT UI FROM DASHBOARD ---
from dashboard import HTML_LANDING, HTML_DASHBOARD, HTML_TOS, HTML_PRIVACY

# ==========================================
# MASTER ROUTING LOGIC
# ==========================================

@app.route('/')
def home():
    return render_template_string(HTML_LANDING)

@app.route('/login')
def login():
    return redirect(OAUTH_URL)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code: return "Error: No code provided", 400

    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(f"{API_BASE}/oauth2/token", data=data, headers=headers)
    
    if r.status_code != 200: return f"Login Failed: {r.text}", 400
        
    session['token'] = r.json().get('access_token')
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'token' not in session: return redirect(url_for('home'))
    
    headers = {'Authorization': f"Bearer {session['token']}"}
    user_req = requests.get(f"{API_BASE}/users/@me", headers=headers)
    guilds_req = requests.get(f"{API_BASE}/users/@me/guilds", headers=headers)

    if user_req.status_code != 200:
        session.clear()
        return redirect(url_for('home'))

    # Filter for servers where you have Admin permissions (Permission 0x8)
    try:
        all_guilds = guilds_req.json()
        admin_servers = [g for g in all_guilds if (int(g.get('permissions', 0)) & 0x8) == 0x8]
    except Exception as e:
        print(f"Error parsing guilds: {e}")
        admin_servers = []
    
    return render_template_string(HTML_DASHBOARD, user=user_req.json(), servers=admin_servers)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/health')
def health():
    return "Master Brain is Online!", 200

# ==========================================
# BOT BACKGROUND THREAD
# ==========================================

def run_bot():
    token = os.getenv('DISCORD_TOKEN')
    print("⏳ Bot thread waiting for network...", flush=True)
    time.sleep(15) 
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        print("🟢 Bot is attempting to log in...", flush=True)
        bot.run(token)
    except Exception as e:
        print(f"🔴 Bot Error: {e}", flush=True)
        os._exit(1)

if __name__ == "__main__":
    print("🟢 Master script starting!", flush=True)
    
    # Start Bot in background
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Start Web Server in main thread
    port = int(os.environ.get("PORT", 10000))
    print(f"🟢 Flask starting on port {port}...", flush=True)
    app.run(host='0.0.0.0', port=port)