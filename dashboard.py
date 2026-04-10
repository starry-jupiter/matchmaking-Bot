import os
import urllib.parse
import requests
from flask import Flask, render_template_string, redirect, request, session, url_for
from dotenv import load_dotenv

import database
from admin import admin_bp  

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-key-change-me")

# Register the admin panel so Flask knows it exists
app.register_blueprint(admin_bp)

# --- DISCORD OAUTH2 SETTINGS ---
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")

# 🚨 PUT YOUR NEW FRANKFURT WORKSPACE URL HERE 🚨
REDIRECT_URI = "https://matchmaking-bot-q2v5.onrender.com"

# Safely encode the URL so Discord doesn't complain
encoded_uri = urllib.parse.quote(REDIRECT_URI, safe='')
OAUTH_URL = f"https://discord.com/oauth2/authorize?client_id=1492121294819557436&response_type=code&redirect_uri=https%3A%2F%2Fmatchmaking-bot-q2v5.onrender.com%2Fcallback&scope=identify+guilds"
DISCORD_API_BASE = "https://discord.com/api/v10"

# ==========================================
# 1. HTML TEMPLATES
# ==========================================
HTML_LANDING = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Matchmaker | The Ultimate Discord Dating Bot</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        body { font-family: 'Inter', sans-serif; background-color: #0f1015; color: #ffffff; overflow-x: hidden; }
        .neon-text { text-shadow: 0 0 20px rgba(168, 85, 247, 0.8); }
        .glass-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); backdrop-filter: blur(12px); }
        .bg-blob { position: absolute; filter: blur(100px); z-index: -1; opacity: 0.4; }
    </style>
</head>
<body class="min-h-screen flex flex-col selection:bg-purple-500 selection:text-white relative">
    <div class="bg-blob bg-purple-700 w-96 h-96 rounded-full top-0 left-0 -translate-x-1/2 -translate-y-1/2"></div>
    <div class="bg-blob bg-blue-900 w-96 h-96 rounded-full bottom-0 right-0 translate-x-1/3 translate-y-1/3"></div>

    <nav class="w-full max-w-7xl mx-auto flex justify-between items-center py-6 px-8 relative z-10">
        <div class="text-2xl font-black tracking-tighter text-purple-500 neon-text">MATCHMAKER<span class="text-white">.BOT</span></div>
        <div class="hidden md:flex gap-8 font-bold text-gray-400">
            <a href="/tos" class="hover:text-purple-400 transition-colors">Terms of Service</a>
            <a href="/privacy" class="hover:text-purple-400 transition-colors">Privacy Policy</a>
        </div>
        <a href="/login" class="bg-[#5865F2] hover:bg-[#4752C4] text-white font-bold py-2 px-5 rounded-lg transition-all flex items-center gap-2 shadow-[0_0_15px_rgba(88,101,242,0.4)]">
            Login with Discord
        </a>
    </nav>

    <main class="flex-grow flex flex-col items-center justify-center w-full px-8 mt-20 relative z-10 text-center">
        <div class="inline-block bg-purple-500/10 text-purple-400 text-sm font-bold uppercase tracking-wider px-4 py-1.5 rounded-full border border-purple-500/20 mb-6">
            Now Live For Discord Servers
        </div>
        <h1 class="text-5xl md:text-7xl font-black mb-6 tracking-tight leading-tight">
            Find your perfect match. <br>Right inside <span class="text-purple-500 neon-text">Discord.</span>
        </h1>
        <p class="text-gray-400 text-lg md:text-xl mb-12 max-w-2xl mx-auto">
            An advanced, AI-normalized swiping ecosystem for your community.
        </p>
        <a href="/login" class="inline-block bg-purple-600 hover:bg-purple-500 text-white text-xl font-bold py-4 px-12 rounded-xl shadow-[0_0_25px_rgba(168,85,247,0.5)] transition-all hover:-translate-y-1">
            Open Dashboard
        </a>
    </main>
    
    <footer class="w-full border-t border-white/5 py-8 mt-auto relative z-10 text-center text-gray-500 text-sm">
        <div class="flex justify-center gap-6 mb-4 md:hidden">
            <a href="/tos" class="hover:text-purple-400 transition-colors">Terms of Service</a>
            <a href="/privacy" class="hover:text-purple-400 transition-colors">Privacy Policy</a>
        </div>
        <p>&copy; 2026 Matchmaker Bot. All rights reserved.</p>
    </footer>
</body>
</html>
"""

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Matchmaker | Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        body { font-family: 'Inter', sans-serif; background-color: #0f1015; color: #ffffff; }
        .neon-text { text-shadow: 0 0 15px rgba(168, 85, 247, 0.7); }
        .glass-card { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); }
    </style>
</head>
<body class="min-h-screen flex flex-col items-center selection:bg-purple-500 selection:text-white relative">
    <nav class="w-full max-w-6xl mx-auto flex justify-between items-center py-6 px-8 border-b border-white/5 relative z-10">
        <a href="/" class="text-2xl font-black tracking-tighter text-purple-500 neon-text cursor-pointer">MATCHMAKER<span class="text-white">.BOT</span></a>
        <div class="flex items-center gap-4">
            <span class="text-gray-400 font-bold hidden md:block">Welcome, {{ user.username }}</span>
            <a href="/logout" class="bg-red-500/20 text-red-400 hover:bg-red-500 hover:text-white font-bold py-2 px-6 rounded-md transition-all">Logout</a>
        </div>
    </nav>
    <main class="flex-grow flex flex-col items-center w-full px-8 mt-12 pb-12 relative z-10">
        <div class="text-center max-w-3xl mb-12">
            <h1 class="text-4xl md:text-5xl font-black mb-4 tracking-tight">Select a <span class="text-purple-500 neon-text">Server</span></h1>
        </div>

        <div class="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {% if servers %}
                {% for server in servers %}
                <a href="/admin/{{ server.id }}" class="glass-card p-6 rounded-2xl hover:border-purple-500/50 hover:-translate-y-1 transition-all flex items-center gap-4 cursor-pointer">
                    {% if server.icon %}
                        <img src="https://cdn.discordapp.com/icons/{{ server.id }}/{{ server.icon }}.png" class="w-12 h-12 rounded-full border border-white/10">
                    {% else %}
                        <div class="w-12 h-12 rounded-full bg-gray-800 border border-white/10 flex items-center justify-center font-bold">{{ server.name[0] }}</div>
                    {% endif %}
                    <div class="overflow-hidden">
                        <h3 class="font-bold text-white truncate w-full">{{ server.name }}</h3>
                        <p class="text-xs text-purple-400 font-bold uppercase tracking-wide">Manage Settings</p>
                    </div>
                </a>
                {% endfor %}
            {% else %}
                <div class="col-span-3 text-center text-gray-500 p-10 glass-card rounded-2xl">
                    <p>You don't have Administrator permissions in any servers!</p>
                </div>
            {% endif %}
        </div>
    </main>
</body>
</html>
"""

HTML_TOS = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Terms of Service | Matchmaker Bot</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { font-family: sans-serif; background-color: #0f1015; color: #ffffff; }
        .glass-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); }
    </style>
</head>
<body class="min-h-screen flex flex-col relative">
    <nav class="w-full max-w-7xl mx-auto flex justify-between items-center py-6 px-8 border-b border-white/5">
        <a href="/" class="text-gray-400 hover:text-white font-bold">&larr; Back to Home</a>
    </nav>
    <main class="flex-grow flex flex-col items-center w-full px-8 mt-12 mb-20">
        <div class="w-full max-w-4xl glass-card rounded-3xl p-10 text-gray-300">
            <h1 class="text-4xl font-black mb-2 text-white">Terms of Service</h1>
            <p class="text-purple-400 font-bold mb-10 pb-6 border-b border-white/5">Last Updated: April 8th, 2026</p>
            <p class="mb-8">By using Matchmaker Bot, you agree to these Terms. You must be 13+ to use this bot...</p>
        </div>
    </main>
</body>
</html>
"""

HTML_PRIVACY = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Privacy Policy | Matchmaker Bot</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { font-family: sans-serif; background-color: #0f1015; color: #ffffff; }
        .glass-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); }
    </style>
</head>
<body class="min-h-screen flex flex-col relative">
    <nav class="w-full max-w-7xl mx-auto flex justify-between items-center py-6 px-8 border-b border-white/5">
        <a href="/" class="text-gray-400 hover:text-white font-bold">&larr; Back to Home</a>
    </nav>
    <main class="flex-grow flex flex-col items-center w-full px-8 mt-12 mb-20">
        <div class="w-full max-w-4xl glass-card rounded-3xl p-10 text-gray-300">
            <h1 class="text-4xl font-black mb-2 text-white">Privacy Policy</h1>
            <p class="text-sky-400 font-bold mb-10 pb-6 border-b border-white/5">Last Updated: April 8th, 2026</p>
            <p class="mb-8">This policy explains how Matchmaker Bot collects your data securely via Supabase...</p>
        </div>
    </main>
</body>
</html>
"""

# ==========================================
@app.route('/')
def home():
    # 🔥 The Auto-Skip logic has been removed here!
    # It will now always render the HTML_LANDING page.
    return render_template_string(HTML_LANDING)

@app.route('/login')
def login():
    return redirect(OAUTH_URL)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code: return "Error: No code provided", 400

    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(f"{DISCORD_API_BASE}/oauth2/token", data=data, headers=headers)
    
    if r.status_code != 200: return f"Failed to login: {r.text}", 400
        
    session['token'] = r.json().get('access_token')
    
    # 🔙 Reverted back to the lobby!
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'token' not in session:
        return redirect(url_for('home'))

    headers = {'Authorization': f"Bearer {session['token']}"}

    user_req = requests.get(f"{DISCORD_API_BASE}/users/@me", headers=headers)
    if user_req.status_code != 200:
        session.clear()
        return redirect(url_for('home'))

    guilds_req = requests.get(f"{DISCORD_API_BASE}/users/@me/guilds", headers=headers)
    all_guilds = guilds_req.json()

    admin_servers = []
    for g in all_guilds:
        if (int(g['permissions']) & 0x8) == 0x8:
            admin_servers.append(g)

    return render_template_string(HTML_DASHBOARD, user=user_req.json(), servers=admin_servers)

@app.route('/tos')
def terms_of_service():
    return render_template_string(HTML_TOS)

@app.route('/privacy')
def privacy_policy():
    return render_template_string(HTML_PRIVACY)

if __name__ == '__main__':
    app.run(debug=True, port=25580)