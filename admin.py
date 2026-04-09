import threading
import os
from flask import Flask
from admin import admin_bp  # This matches the name in your admin.py!
from app import bot         # This imports your Discord bot instance
from dotenv import load_dotenv

load_dotenv()

# 1. Create the actual Flask Application
app = Flask(__name__)

# 2. Register your Admin Dashboard instructions
app.register_blueprint(admin_bp)

# 3. Add a health check so Render knows the site is working
@app.route('/health')
def health():
    return "Matchmaker Dashboard is Online!", 200

def run_flask():
    # Render uses port 10000 by default
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Start the Dashboard in the background
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # Start the Discord Bot in the foreground
    # (Make sure 'bot' is the name of your bot object in app.py)
    bot.run(os.getenv('DISCORD_TOKEN'))

HTML_ADMIN_PANEL = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manage {{ server_name }} | Matchmaker Bot</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
    .discord-embed-mock {
            background-color: #2b2d31;
            border-left: 4px solid #6b48ff;
            border-radius: 4px;
            padding: 12px 16px;
            max-width: 520px;
        }
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&display=swap');
        body { font-family: 'Inter', sans-serif; background-color: #111216; color: #ffffff; }
        
        input, select, textarea { 
            background-color: #22242a; border: 1px solid rgba(255,255,255,0.05); color: white; 
            width: 100%; padding: 0.75rem 1rem; border-radius: 0.5rem; outline: none; transition: all 0.2s;
            appearance: none;
        }
        input[type="date"]::-webkit-calendar-picker-indicator { filter: invert(1); cursor: pointer; }
        input:focus, select:focus, textarea:focus { border-color: #6b48ff; box-shadow: 0 0 0 2px rgba(107, 72, 255, 0.2); }
        
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #2a2c36; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #3f4252; }
    </style>
</head>
<body class="flex h-screen overflow-hidden selection:bg-[#6b48ff] selection:text-white">
    
    <aside class="w-64 bg-[#18191e] flex flex-col border-r border-white/5 flex-shrink-0 z-20">
        <div class="h-20 px-6 flex items-center gap-3 border-b border-white/5">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-[#6b48ff] to-[#4823db] flex items-center justify-center font-black text-lg shadow-lg">{{ server_name[0] }}</div>
            <span class="font-bold text-lg truncate">{{ server_name }}</span>
        </div>
        
        <nav class="flex-1 p-4 space-y-1 overflow-y-auto" id="sidebar-nav">
        
            <a href="/dashboard" class="flex items-center gap-3 text-gray-400 hover:text-white px-4 py-3 rounded-xl transition-all hover:bg-white/5 mb-4">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
                Back to Servers
            </a>
            
            <p class="text-xs font-black text-emerald-500 uppercase tracking-widest px-4 mt-6 mb-2">Overview</p>
            <button type="button" onclick="switchTab('analytics')" id="btn-analytics" class="w-full flex items-center gap-3 text-emerald-400 bg-emerald-500/10 px-4 py-3 rounded-xl border-l-4 border-emerald-500 transition-all font-bold">
                📈 Live Statistics
            </button>

            <button type="button" onclick="switchTab('embed')" id="btn-embed" class="w-full flex items-center gap-3 text-gray-400 hover:text-white hover:bg-white/5 px-4 py-3 rounded-xl border-l-4 border-transparent transition-all font-bold">
                🎨 Embed Builder
            </button>

            <p class="text-xs font-black text-purple-500 uppercase tracking-widest px-4 mt-8 mb-2">Configuration</p>
            <button type="button" onclick="switchTab('game')" id="btn-game" class="w-full flex items-center gap-3 text-gray-400 hover:text-white hover:bg-white/5 px-4 py-3 rounded-xl border-l-4 border-transparent transition-all font-bold">
                🎮 Game Settings
            </button>
            <button type="button" onclick="switchTab('safety')" id="btn-safety" class="w-full flex items-center gap-3 text-gray-400 hover:text-white hover:bg-white/5 px-4 py-3 rounded-xl border-l-4 border-transparent transition-all font-bold">
                🛡️ Safety
            </button>
            <button type="button" onclick="switchTab('core')" id="btn-core" class="w-full flex items-center gap-3 text-gray-400 hover:text-white hover:bg-white/5 px-4 py-3 rounded-xl border-l-4 border-transparent transition-all font-bold">
                ⚙️ Channels & Roles
            </button>
        </nav>
    </aside>

    <main class="flex-1 flex flex-col h-full overflow-hidden bg-[#111216] relative">
        <header class="h-20 px-8 flex items-center justify-between border-b border-white/5 bg-[#111216]/80 backdrop-blur-md sticky top-0 z-10">
            <div class="text-sm font-medium text-gray-400">Dashboard / <span class="text-white" id="header-title">Live Statistics</span></div>
        </header>

        <div class="flex-1 overflow-y-auto p-8 w-full max-w-5xl mx-auto pb-32">
            
            <div class="w-full bg-gradient-to-r from-[#6b48ff] to-[#4823db] rounded-2xl p-8 mb-8 shadow-2xl flex justify-between items-center">
                <div>
                    <h1 class="text-3xl font-black mb-1 text-white">Server Dashboard</h1>
                    <p class="text-purple-200">Track growth and configure your matchmaking ecosystem.</p>
                </div>
                <button type="submit" form="settingsForm" name="action" value="save" class="bg-white text-[#6b48ff] font-bold py-3 px-8 rounded-xl hover:scale-105 transition-all shadow-lg">
                    💾 Save All Changes
                </button>
            </div>

            {% if success_msg %}
            <div class="bg-green-500/10 border border-green-500/50 text-green-400 font-bold p-4 rounded-xl mb-8 flex items-center gap-3">
                {{ success_msg }}
            </div>
            {% endif %}

            <div id="tab-analytics" class="tab-content block">
                <h2 class="text-2xl font-bold mb-6 text-emerald-400 flex items-center gap-2">📈 Matchmaking Analytics</h2>
                
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    
                    <button onclick="showDataView('users')" class="text-left bg-[#18191e] border border-emerald-500/20 rounded-2xl p-5 shadow-lg hover:bg-[#20222a] hover:-translate-y-1 hover:shadow-emerald-900/20 transition-all relative overflow-hidden group">
                        <div class="absolute -right-4 -top-4 text-6xl opacity-10 group-hover:scale-110 transition-transform">👥</div>
                        <h3 class="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">Users in Pool</h3>
                        <div class="text-3xl font-black text-white">{{ stats.total_users }}</div>
                        <div class="text-emerald-400 text-xs font-bold mt-2">Click to view table →</div>
                    </button>
                    
                    <button onclick="showDataView('active_pairs')" class="text-left bg-[#18191e] border border-pink-500/20 rounded-2xl p-5 shadow-lg hover:bg-[#20222a] hover:-translate-y-1 hover:shadow-pink-900/20 transition-all relative overflow-hidden group">
                        <div class="absolute -right-4 -top-4 text-6xl opacity-10 group-hover:scale-110 transition-transform">☕</div>
                        <h3 class="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">Active </h3>
                        <div class="text-3xl font-black text-white">{{ stats.active_pairs }}</div>
                        <div class="text-pink-400 text-xs font-bold mt-2">Click to view table →</div>
                    </button>

                    <button onclick="showDataView('swipes')" class="text-left bg-[#18191e] border border-sky-500/20 rounded-2xl p-5 shadow-lg hover:bg-[#20222a] hover:-translate-y-1 hover:shadow-sky-900/20 transition-all relative overflow-hidden group">
                        <div class="absolute -right-4 -top-4 text-6xl opacity-10 group-hover:scale-110 transition-transform">🔥</div>
                        <h3 class="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">Total Swipes</h3>
                        <div class="text-3xl font-black text-white">{{ stats.total_swipes }}</div>
                        <div class="text-sky-400 text-xs font-bold mt-2">Click to view log →</div>
                    </button>

                    <button onclick="showDataView('unpairs')" class="text-left bg-[#18191e] border border-rose-500/20 rounded-2xl p-5 shadow-lg hover:bg-[#20222a] hover:-translate-y-1 hover:shadow-rose-900/20 transition-all relative overflow-hidden group">
                        <div class="absolute -right-4 -top-4 text-6xl opacity-10 group-hover:scale-110 transition-transform">💔</div>
                        <h3 class="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">Total Unpairs</h3>
                        <div class="text-3xl font-black text-white">{{ stats.total_unpairs }}</div>
                        <div class="text-rose-400 text-xs font-bold mt-2">Click to view log →</div>
                    </button>

                </div>

                <div class="bg-[#18191e] border border-white/5 rounded-2xl shadow-lg overflow-hidden">
                    
                    <div id="data-view-chart" class="data-view-panel p-6 block">
                        <h3 class="text-gray-400 text-sm font-bold uppercase tracking-wider mb-4">Engagement (Last 7 Days)</h3>
                        <canvas id="activityChart" height="80"></canvas>
                    </div>

                    <div id="data-view-users" class="data-view-panel hidden">
                        <div class="flex justify-between items-center bg-white/5 p-4 border-b border-white/5">
                            <h3 class="text-white font-bold">👥 User Database</h3>
                            <div class="flex gap-3">
                                <input type="date" onchange="filterTable('usersTable', this.value)" class="bg-[#22242a] border border-white/10 rounded px-2 py-1 text-xs text-gray-300">
                                <button onclick="sortTable('usersTable')" class="text-xs bg-gray-700 hover:bg-gray-600 text-white px-3 py-1 rounded">Sort Date ↕</button>
                                <button onclick="showDataView('chart')" class="text-xs bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1 rounded">Close</button>
                            </div>
                        </div>
                        <div class="overflow-x-auto max-h-96">
                            <table id="usersTable" class="w-full text-left text-sm text-gray-400">
                                <thead class="bg-white/5 text-gray-300 uppercase text-xs sticky top-0">
                                    <tr><th class="p-4">Discord User</th><th class="p-4">Profile Name</th><th class="p-4">Age/Gender</th><th class="p-4">Time Created</th></tr>
                                </thead>
                                <tbody>
                                    {% for u in users_data %}
                                    {% set m = member_map.get(u.user_id|string, {}) %}
                                    <tr class="border-b border-white/5 hover:bg-white/5 transition-colors">
                                        <td class="p-4 flex items-center gap-3">
                                            <img src="{{ m.avatar or 'https://cdn.discordapp.com/embed/avatars/0.png' }}" class="w-8 h-8 rounded-full border border-white/10">
                                            <div class="flex flex-col">
                                                <span class="text-white font-bold">{{ m.username or 'Unknown' }}</span>
                                                <span class="text-xs text-gray-500">{{ u.user_id }}</span>
                                            </div>
                                        </td>
                                        <td class="p-4 text-emerald-400 font-bold">{{ u.name }}</td>
                                        <td class="p-4">{{ u.age }} | {{ u.gender | title }}</td>
                                        <td class="p-4 date-cell whitespace-nowrap">{{ u.created_at[:10] if u.created_at else '2026-01-01' }} <span class="text-xs text-gray-500">{{ u.created_at[11:16] if u.created_at else '00:00' }}</span></td>
                                    </tr>
                                    {% else %}
                                    <tr><td colspan="4" class="p-6 text-center text-gray-500">No users found.</td></tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div id="data-view-active_pairs" class="data-view-panel hidden">
                        <div class="flex justify-between items-center bg-white/5 p-4 border-b border-white/5">
                            <h3 class="text-white font-bold">☕ Active Cafes</h3>
                            <div class="flex gap-3">
                                <input type="date" onchange="filterTable('pairsTable', this.value)" class="bg-[#22242a] border border-white/10 rounded px-2 py-1 text-xs text-gray-300">
                                <button onclick="sortTable('pairsTable')" class="text-xs bg-gray-700 hover:bg-gray-600 text-white px-3 py-1 rounded">Sort Date ↕</button>
                                <button onclick="showDataView('chart')" class="text-xs bg-pink-600 hover:bg-pink-500 text-white px-3 py-1 rounded">Close</button>
                            </div>
                        </div>
                        <div class="overflow-x-auto max-h-96">
                            <table id="pairsTable" class="w-full text-left text-sm text-gray-400">
                                <thead class="bg-white/5 text-gray-300 uppercase text-xs sticky top-0">
                                    <tr><th class="p-4">User 1</th><th class="p-4">User 2</th><th class="p-4">Date Matched</th></tr>
                                </thead>
                                <tbody>
                                    {% for p in pairs_data %}
                                    {% set m1 = member_map.get(p.user1_id|string, {}) %}
                                    {% set m2 = member_map.get(p.user2_id|string, {}) %}
                                    <tr class="border-b border-white/5 hover:bg-white/5 transition-colors">
                                        <td class="p-4">
                                            <div class="flex items-center gap-2">
                                                <img src="{{ m1.avatar or 'https://cdn.discordapp.com/embed/avatars/1.png' }}" class="w-6 h-6 rounded-full">
                                                <span class="text-white">{{ m1.username or p.user1_id }}</span>
                                            </div>
                                        </td>
                                        <td class="p-4">
                                            <div class="flex items-center gap-2">
                                                <img src="{{ m2.avatar or 'https://cdn.discordapp.com/embed/avatars/2.png' }}" class="w-6 h-6 rounded-full">
                                                <span class="text-white">{{ m2.username or p.user2_id }}</span>
                                            </div>
                                        </td>
                                        <td class="p-4 date-cell whitespace-nowrap">{{ p.start_time[:10] if p.start_time else '2026-01-01' }} <span class="text-xs text-gray-500">{{ p.start_time[11:16] if p.start_time else '00:00' }}</span></td>
                                    </tr>
                                    {% else %}
                                    <tr><td colspan="3" class="p-6 text-center text-gray-500">No active pairs right now.</td></tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div id="data-view-swipes" class="data-view-panel hidden">
                        <div class="flex justify-between items-center bg-white/5 p-4 border-b border-white/5">
                            <h3 class="text-white font-bold">🔥 Recent Swipes</h3>
                            <div class="flex gap-3">
                                <input type="date" onchange="filterTable('swipesTable', this.value)" class="bg-[#22242a] border border-white/10 rounded px-2 py-1 text-xs text-gray-300">
                                <button onclick="sortTable('swipesTable')" class="text-xs bg-gray-700 hover:bg-gray-600 text-white px-3 py-1 rounded">Sort Date ↕</button>
                                <button onclick="showDataView('chart')" class="text-xs bg-sky-600 hover:bg-sky-500 text-white px-3 py-1 rounded">Close</button>
                            </div>
                        </div>
                        <div class="overflow-x-auto max-h-96">
                            <table id="swipesTable" class="w-full text-left text-sm text-gray-400">
                                <thead class="bg-white/5 text-gray-300 uppercase text-xs sticky top-0">
                                    <tr><th class="p-4">Swiper</th><th class="p-4">Target Profile</th><th class="p-4">Action</th><th class="p-4">Time</th></tr>
                                </thead>
                                <tbody>
                                    {% for s in swipes_data %}
                                    {% set m1 = member_map.get(s.user_id|string, {}) %}
                                    {% set m2 = member_map.get(s.target_id|string, {}) %}
                                    <tr class="border-b border-white/5 hover:bg-white/5 transition-colors">
                                        <td class="p-4 flex items-center gap-2">
                                            <img src="{{ m1.avatar or 'https://cdn.discordapp.com/embed/avatars/3.png' }}" class="w-6 h-6 rounded-full">
                                            <span class="text-white">{{ m1.username or s.user_id }}</span>
                                        </td>
                                        <td class="p-4 text-white">{{ m2.username or s.target_id }}</td>
                                        <td class="p-4 font-bold {% if s.liked %}text-emerald-400{% else %}text-rose-400{% endif %}">
                                            {% if s.liked %}Right Swipe (Liked){% else %}Left Swipe (Passed){% endif %}
                                        </td>
                                        <td class="p-4 date-cell whitespace-nowrap">{{ s.created_at[:10] if s.created_at else '2026-01-01' }} <span class="text-xs text-gray-500">{{ s.created_at[11:16] if s.created_at else '00:00' }}</span></td>
                                    </tr>
                                    {% else %}
                                    <tr><td colspan="4" class="p-6 text-center text-gray-500">No swipes logged yet.</td></tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div id="data-view-unpairs" class="data-view-panel hidden">
                        <div class="flex justify-between items-center bg-white/5 p-4 border-b border-white/5">
                            <h3 class="text-white font-bold">💔 Broken Matches</h3>
                            <div class="flex gap-3">
                                <input type="date" onchange="filterTable('unpairsTable', this.value)" class="bg-[#22242a] border border-white/10 rounded px-2 py-1 text-xs text-gray-300">
                                <button onclick="sortTable('unpairsTable')" class="text-xs bg-gray-700 hover:bg-gray-600 text-white px-3 py-1 rounded">Sort Date ↕</button>
                                <button onclick="showDataView('chart')" class="text-xs bg-rose-600 hover:bg-rose-500 text-white px-3 py-1 rounded">Close</button>
                            </div>
                        </div>
                        <div class="overflow-x-auto max-h-96">
                            <table id="unpairsTable" class="w-full text-left text-sm text-gray-400">
                                <thead class="bg-white/5 text-gray-300 uppercase text-xs sticky top-0">
                                    <tr><th class="p-4">User 1</th><th class="p-4">User 2</th><th class="p-4">Date Ended</th></tr>
                                </thead>
                                <tbody>
                                    {% for up in unpairs_data %}
                                    {% set m1 = member_map.get(up.user1_id|string, {}) %}
                                    {% set m2 = member_map.get(up.user2_id|string, {}) %}
                                    <tr class="border-b border-white/5 hover:bg-white/5 transition-colors">
                                        <td class="p-4">
                                            <div class="flex items-center gap-2">
                                                <img src="{{ m1.avatar or 'https://cdn.discordapp.com/embed/avatars/4.png' }}" class="w-6 h-6 rounded-full">
                                                <span class="text-white">{{ m1.username or up.user1_id }}</span>
                                            </div>
                                        </td>
                                        <td class="p-4">
                                            <div class="flex items-center gap-2">
                                                <img src="{{ m2.avatar or 'https://cdn.discordapp.com/embed/avatars/0.png' }}" class="w-6 h-6 rounded-full">
                                                <span class="text-white">{{ m2.username or up.user2_id }}</span>
                                            </div>
                                        </td>
                                        <td class="p-4 date-cell text-rose-400 whitespace-nowrap">{{ up.end_time[:10] if up.end_time else '2026-01-01' }} <span class="text-xs text-gray-500">{{ up.end_time[11:16] if up.end_time else '00:00' }}</span></td>
                                    </tr>
                                    {% else %}
                                    <tr><td colspan="3" class="p-6 text-center text-gray-500">No broken matches yet!</td></tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>

                </div>
            </div>
<div id="tab-embed" class="tab-content hidden">
                <h1 class="text-3xl font-black mb-8 text-sky-400">Visual Embed Builder</h1>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-10">
                    <div class="space-y-4 bg-[#18191e] p-6 rounded-2xl border border-white/5">
                        <div>
                            <label class="text-[10px] font-bold text-gray-500 uppercase">Title</label>
                            <input type="text" id="emb-title" oninput="updatePreview()" placeholder="Embed Title">
                        </div>
                        <div>
                            <label class="text-[10px] font-bold text-gray-500 uppercase">Hex Color</label>
                            <input type="text" id="emb-color" oninput="updatePreview()" value="#6b48ff">
                        </div>
                        <div>
                            <label class="text-[10px] font-bold text-gray-500 uppercase">Description</label>
                            <textarea id="emb-desc" oninput="updatePreview()" rows="5" placeholder="Description..."></textarea>
                        </div>
                        <div>
                            <label class="text-[10px] font-bold text-gray-500 uppercase">Image URL</label>
                            <input type="text" id="emb-image" oninput="updatePreview()" placeholder="https://...">
                        </div>
                    </div>
                    <div class="space-y-4">
                        <label class="text-[10px] font-bold text-gray-500 uppercase">Discord Preview</label>
                        <div class="discord-embed-mock" id="preview-container">
                            <div class="font-bold text-[16px] mb-1 text-white" id="pre-title">Embed Title</div>
                            <div class="text-[14px] text-[#dbdee1] whitespace-pre-wrap" id="pre-desc">Your text here...</div>
                            <img src="" id="pre-image" class="mt-3 rounded-md hidden max-h-[300px] w-full object-cover">
                        </div>
                    </div>
                </div>
            </div>
            <form id="settingsForm" method="POST" action="/admin/{{ guild_id }}">
                <div id="tab-game" class="tab-content hidden">
                    <h2 class="text-2xl font-bold mb-4 text-white flex items-center gap-2">💎 Bot Branding <span class="text-xs bg-amber-500/20 text-amber-500 px-2 py-1 rounded ml-2">PRO</span></h2>
                    <div class="bg-[#18191e] border border-white/5 rounded-2xl p-8 mb-10 shadow-xl">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label class="text-xs font-bold text-sky-500 uppercase mb-2 block">Custom Bot Name</label>
                                <input type="text" name="custom_bot_name" value="{{ config.custom_bot_name or '' }}" placeholder="e.g. MyServer Dating Bot">
                            </div>
                            <div>
                                <label class="text-xs font-bold text-sky-500 uppercase mb-2 block">Custom Welcome Message</label>
                                <textarea name="custom_welcome_msg" rows="2" placeholder="Welcome to the matchmaking zone!">{{ config.custom_welcome_msg or '' }}</textarea>
                            </div>
                        </div>
                    </div>
                    <h2 class="text-2xl font-bold mb-4">🎮 Gameplay Rules</h2>
                    <div class="bg-[#18191e] border border-white/5 rounded-2xl p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label class="text-xs font-bold text-gray-500 uppercase mb-2 block">AI Icebreaker Vibe</label>
                            <select name="icebreaker_vibe">
                                <option value="Casual" {% if config.icebreaker_vibe == 'Casual' %}selected{% endif %}>Casual & Friendly</option>
                                <option value="Romantic" {% if config.icebreaker_vibe == 'Romantic' %}selected{% endif %}>Romantic & Flirty</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-xs font-bold text-gray-500 uppercase mb-2 block">Match Duration</label>
                            <select name="match_duration">
                                <option value="7" {% if config.match_duration == 7 %}selected{% endif %}>7 Days</option>
                                <option value="14" {% if config.match_duration == 14 %}selected{% endif %}>14 Days</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div id="tab-safety" class="tab-content hidden">
                    <h2 class="text-2xl font-bold mb-6">🛡️ Safety & Moderation</h2>
                    <div class="bg-[#18191e] border border-white/5 rounded-2xl p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label class="text-xs font-bold text-gray-500 uppercase mb-2 block">Minimum Age</label>
                            <select name="min_age">
                                <option value="13" {% if config.min_age == 13 %}selected{% endif %}>13+ (Discord Default)</option>
                                <option value="18" {% if config.min_age == 18 %}selected{% endif %}>18+ (Adults Only)</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-xs font-bold text-gray-500 uppercase mb-2 block">Require Staff Approval</label>
                            <select name="require_approval">
                                <option value="false" {% if not config.require_approval %}selected{% endif %}>No (Instant Join)</option>
                                <option value="true" {% if config.require_approval %}selected{% endif %}>Yes (Manual Queue)</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div id="tab-core" class="tab-content hidden">
                    <h2 class="text-2xl font-bold mb-6">⚙️ Channels & Roles</h2>
                    <div class="bg-[#18191e] border border-white/5 rounded-2xl p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div><label class="text-xs font-bold text-sky-500 uppercase mb-2 block">Ticket Category</label><select name="match_category_id"><option value="">-- Select Category --</option>{% for cat in categories %}<option value="{{ cat.id }}" {% if config.match_category_id == cat.id %}selected{% endif %}>📁 {{ cat.name }}</option>{% endfor %}</select></div>
                        <div><label class="text-xs font-bold text-sky-500 uppercase mb-2 block">Private Cafe Category</label><select name="cafe_category_id"><option value="">-- Select Category --</option>{% for cat in categories %}<option value="{{ cat.id }}" {% if config.cafe_category_id == cat.id %}selected{% endif %}>📁 {{ cat.name }}</option>{% endfor %}</select></div>
                        <div><label class="text-xs font-bold text-sky-500 uppercase mb-2 block">Pairs Announcement Channel</label><select name="pairs_channel_id"><option value="">-- Select Channel --</option>{% for ch in text_channels %}<option value="{{ ch.id }}" {% if config.pairs_channel_id == ch.id %}selected{% endif %}># {{ ch.name }}</option>{% endfor %}</select></div>
                        <div><label class="text-xs font-bold text-sky-500 uppercase mb-2 block">Staff Log Channel</label><select name="staff_channel_id"><option value="">-- Select Channel --</option>{% for ch in text_channels %}<option value="{{ ch.id }}" {% if config.staff_channel_id == ch.id %}selected{% endif %}># {{ ch.name }}</option>{% endfor %}</select></div>
                        <div><label class="text-xs font-bold text-sky-500 uppercase mb-2 block">Paired Role</label><select name="paired_role_id"><option value="">-- Select Role --</option>{% for r in roles %}<option value="{{ r.id }}" {% if config.paired_role_id == r.id %}selected{% endif %}>@ {{ r.name }}</option>{% endfor %}</select></div>
                        <div><label class="text-xs font-bold text-sky-500 uppercase mb-2 block">Unpaired Role</label><select name="unpaired_role_id"><option value="">-- Select Role --</option>{% for r in roles %}<option value="{{ r.id }}" {% if config.unpaired_role_id == r.id %}selected{% endif %}>@ {{ r.name }}</option>{% endfor %}</select></div>
                    </div>
                </div>
            </form>
        </div>
    </main>

    <script>
        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => { el.classList.remove('block'); el.classList.add('hidden'); });
            document.getElementById('tab-' + tabId).classList.remove('hidden');
            document.getElementById('tab-' + tabId).classList.add('block');

            const buttons = ['analytics', 'game', 'safety', 'core'];
            buttons.forEach(id => { document.getElementById('btn-' + id).className = "w-full flex items-center gap-3 text-gray-400 hover:text-white hover:bg-white/5 px-4 py-3 rounded-xl border-l-4 border-transparent transition-all font-bold"; });

            const activeBtn = document.getElementById('btn-' + tabId);
            if (tabId === 'analytics') { activeBtn.className = "w-full flex items-center gap-3 text-emerald-400 bg-emerald-500/10 px-4 py-3 rounded-xl border-l-4 border-emerald-500 transition-all font-bold"; } 
            else { activeBtn.className = "w-full flex items-center gap-3 text-[#6b48ff] bg-[#6b48ff]/10 px-4 py-3 rounded-xl border-l-4 border-[#6b48ff] transition-all font-bold"; }
            
            let title = 'Settings';
            if (tabId === 'analytics') title = 'Live Statistics';
            if (tabId === 'game') title = 'Game Settings';
            if (tabId === 'safety') title = 'Safety & Moderation';
            if (tabId === 'core') title = 'Channels & Roles';
            document.getElementById('header-title').innerText = title;
        }

        function showDataView(viewName) {
            document.querySelectorAll('.data-view-panel').forEach(el => { el.classList.remove('block'); el.classList.add('hidden'); });
            document.getElementById('data-view-' + viewName).classList.remove('hidden');
            document.getElementById('data-view-' + viewName).classList.add('block');
        }

        // Vanilla JS Filter by Date
        function filterTable(tableId, dateStr) {
            const rows = document.querySelectorAll(`#${tableId} tbody tr`);
            rows.forEach(row => {
                if (!dateStr) { row.style.display = ''; return; }
                const cell = row.querySelector('.date-cell');
                if (cell && cell.innerText.trim().startsWith(dateStr)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }

        // Vanilla JS Sort by Date
        let sortAsc = {};
        function sortTable(tableId) {
            const table = document.getElementById(tableId);
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            sortAsc[tableId] = !sortAsc[tableId];
            const dir = sortAsc[tableId] ? 1 : -1;

            rows.sort((a, b) => {
                const aCell = a.querySelector('.date-cell');
                const bCell = b.querySelector('.date-cell');
                if(!aCell || !bCell) return 0;
                const aTime = new Date(aCell.innerText.trim()).getTime() || 0;
                const bTime = new Date(bCell.innerText.trim()).getTime() || 0;
                return (aTime - bTime) * dir;
            });
            rows.forEach(row => tbody.appendChild(row));
        }

        const ctx = document.getElementById('activityChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Swipes',
                    data: [12, 19, 30, 25, 42, 60, 55],
                    borderColor: '#6b48ff',
                    backgroundColor: 'rgba(107, 72, 255, 0.1)',
                    borderWidth: 3, tension: 0.4, fill: true,
                    pointBackgroundColor: '#fff', pointBorderColor: '#6b48ff', pointBorderWidth: 2, pointRadius: 4
                }]
            },
            options: {
                responsive: true, plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false, color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af' } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af' }, beginAtZero: true }
                }
            }
        });
    </script>
</body>
</html>
"""

@admin_bp.route('/admin/<guild_id>', methods=['GET', 'POST'])
def manage_server(guild_id):
    if 'token' not in session: return redirect(url_for('home'))

    headers = {'Authorization': f"Bearer {session['token']}"}
    guilds_req = requests.get(f"{DISCORD_API_BASE}/users/@me/guilds", headers=headers)
    if guilds_req.status_code != 200: return redirect(url_for('home'))

    server_info = next((g for g in guilds_req.json() if str(g['id']) == str(guild_id) and (int(g['permissions']) & 0x8) == 0x8), None)
    if not server_info: return "Unauthorized.", 403

    bot_token = os.getenv('DISCORD_TOKEN')
    categories, text_channels, roles, member_map = [], [], [], {}

    if bot_token:
        bot_headers = {"Authorization": f"Bot {bot_token}"}
        channels_req = requests.get(f"{DISCORD_API_BASE}/guilds/{guild_id}/channels", headers=bot_headers)
        roles_req = requests.get(f"{DISCORD_API_BASE}/guilds/{guild_id}/roles", headers=bot_headers)
        
        # --- NEW: Fetching Discord Members to get Avatars & Usernames ---
        members_req = requests.get(f"{DISCORD_API_BASE}/guilds/{guild_id}/members?limit=1000", headers=bot_headers)
        if members_req.status_code == 200:
            for m in members_req.json():
                user = m.get('user', {})
                uid = user.get('id')
                avatar = user.get('avatar')
                username = user.get('username')
                avatar_url = f"https://cdn.discordapp.com/avatars/{uid}/{avatar}.png" if avatar else f"https://cdn.discordapp.com/embed/avatars/{int(uid) % 5}.png"
                member_map[str(uid)] = {'username': username, 'avatar': avatar_url}

        if channels_req.status_code == 200:
            channels = channels_req.json()
            categories = [c for c in channels if c.get('type') == 4]
            text_channels = [c for c in channels if c.get('type') == 0]
        if roles_req.status_code == 200:
            roles = [r for r in roles_req.json() if str(r['id']) != str(guild_id)]

    success_msg = None

    if request.method == 'POST':
        new_config = {
            "match_category_id": request.form.get('match_category_id'),
            "cafe_category_id": request.form.get('cafe_category_id'),
            "pairs_channel_id": request.form.get('pairs_channel_id'),
            "staff_channel_id": request.form.get('staff_channel_id'),
            "paired_role_id": request.form.get('paired_role_id'),
            "unpaired_role_id": request.form.get('unpaired_role_id'),
            "min_age": int(request.form.get('min_age', 13)),
            "require_approval": request.form.get('require_approval') == 'true',
            "icebreaker_vibe": request.form.get('icebreaker_vibe', 'Casual'),
            "match_duration": int(request.form.get('match_duration', 14)),
            "custom_bot_name": request.form.get('custom_bot_name'),
            "custom_welcome_msg": request.form.get('custom_welcome_msg')
        }
        database.update_config(guild_id, new_config)
        success_msg = "✅ Configuration saved successfully!"

    current_config = database.get_config(guild_id) or {}

    # --- FETCHING DATA FOR THE TABLES ---
    users_data, pairs_data, swipes_data, unpairs_data = [], [], [], []
    if hasattr(database, 'supabase'):
        try:
            # Note: order('created_at', desc=True) pulls the newest data first if available in Supabase
            u_res = database.supabase.table('users').select('*').eq('guild_id', str(guild_id)).limit(100).execute()
            if u_res.data: users_data = u_res.data
            
            p_res = database.supabase.table('pairings').select('*').eq('guild_id', str(guild_id)).eq('active', True).limit(50).execute()
            if p_res.data: pairs_data = p_res.data
            
            up_res = database.supabase.table('pairings').select('*').eq('guild_id', str(guild_id)).eq('active', False).limit(50).execute()
            if up_res.data: unpairs_data = up_res.data
            
            s_res = database.supabase.table('swipes').select('*').eq('guild_id', str(guild_id)).limit(50).execute()
            if s_res.data: swipes_data = s_res.data
        except: pass

    live_stats = {
        "total_users": len(users_data),
        "active_pairs": len(pairs_data),
        "total_swipes": len(swipes_data),
        "total_unpairs": len(unpairs_data)
    }

    return render_template_string(
        HTML_ADMIN_PANEL, 
        server_name=server_info['name'], 
        guild_id=guild_id, 
        config=current_config,
        success_msg=success_msg,
        categories=categories,
        text_channels=text_channels,
        roles=roles,
        member_map=member_map, # Passes the Discord Avatars and Usernames to HTML!
        stats=live_stats,
        users_data=users_data,
        pairs_data=pairs_data,
        swipes_data=swipes_data,
        unpairs_data=unpairs_data
    )
