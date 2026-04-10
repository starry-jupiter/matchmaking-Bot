import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# --- SERVER CONFIGURATION ---
def update_config(guild_id, config_data):
    try:
        config_data["guild_id"] = str(guild_id)
        supabase.table("server_configs").upsert(config_data).execute()
        return True
    except Exception as e:
        print(f"Error updating config: {e}")
        return False

def get_config(guild_id):
    try:
        res = supabase.table("server_configs").select("*").eq("guild_id", str(guild_id)).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
    except Exception as e:
        print(f"Error fetching config: {e}")
        return None

# --- PROFILE MANAGEMENT ---
def save_profile(user_id, guild_id, p, raw_text):
    data = {
        "user_id": str(user_id), 
        "guild_id": str(guild_id), 
        "name": p.get("name"),
        "age": p.get("age"), 
        "gender": p.get("gender"), 
        "attracted_to": p.get("attracted_to"), 
        "prns": p.get("prns"), 
        "gmt": p.get("gmt"), 
        "likes": p.get("likes"),
        "dislikes": p.get("dislikes"), 
        "extra": p.get("extra"), 
        "raw_intro": raw_text
    }
    supabase.table("profiles").upsert(data).execute()

def delete_profile(user_id, guild_id):
    try:
        supabase.table("profiles").delete().eq("user_id", str(user_id)).eq("guild_id", str(guild_id)).execute()
        return True
    except Exception as e: return False
    
def get_profile(user_id, guild_id):
    try:
        response = supabase.table("profiles").select("*").eq("user_id", str(user_id)).eq("guild_id", str(guild_id)).execute()
        if response.data and len(response.data) > 0: return response.data[0]
        return None
    except Exception as e: return None

def get_user_by_id(user_id, guild_id):
    return get_profile(user_id, guild_id)

def add_vouch(user_id, guild_id):
    try:
        profile = get_profile(user_id, guild_id)
        if profile:
            current_vouches = profile.get("vouches") or 0
            supabase.table("profiles").update({"vouches": current_vouches + 1}).eq("user_id", str(user_id)).eq("guild_id", str(guild_id)).execute()
            return True
        return False
    except Exception as e: return False

# --- MATCHING & SWIPING ---
def get_strict_matches(user_id, guild_id):
    me_res = supabase.table("profiles").select("*").eq("user_id", str(user_id)).eq("guild_id", str(guild_id)).execute()
    if not me_res.data: return []
    me = me_res.data[0]
    
    others = supabase.table("profiles").select("*").eq("guild_id", str(guild_id)).neq("user_id", str(user_id)).execute().data
    
    matches = []
    for p in others:
        gap = 1 if (me['age'] == 13 or p['age'] == 13) else 2
        if abs(me['age'] - p['age']) > gap: continue
        if me['gender'] not in p['attracted_to'] or p['gender'] not in me['attracted_to']: continue

        my_l = set(x.lower() for x in (me.get('likes') or []))
        my_d = set(x.lower() for x in (me.get('dislikes') or []))
        th_l = set(x.lower() for x in (p.get('likes') or []))
        th_d = set(x.lower() for x in (p.get('dislikes') or []))

        if my_l.intersection(th_d) or th_l.intersection(my_d): continue
        
        shared = my_l.intersection(th_l)
        if len(shared) >= 1:
            p['shared_interests'] = list(shared)
            matches.append(p)
            
    return matches

def record_swipe(user_id, target_id, guild_id, liked):
    try:
        swipe_data = {"user_id": str(user_id), "target_id": str(target_id), "guild_id": str(guild_id), "liked": liked}
        supabase.table("swipes").upsert(swipe_data).execute()
        if liked:
            response = supabase.table("swipes").select("*").eq("user_id", str(target_id)).eq("target_id", str(user_id)).eq("liked", True).execute()
            if response.data and len(response.data) > 0: return True 
        return False 
    except Exception as e: return False

def delete_swipe(user_id, target_id, guild_id):
    try:
        supabase.table("swipes").delete().eq("user_id", str(user_id)).eq("target_id", str(target_id)).execute()
        return True
    except Exception as e: return False

def did_they_like_me(my_id, their_id, guild_id):
    try:
        response = supabase.table("swipes").select("*").eq("user_id", str(their_id)).eq("target_id", str(my_id)).eq("liked", True).execute()
        return len(response.data) > 0
    except Exception as e: return False

# --- PAIRING TIMERS & HISTORY ---
def create_pairing(user1_id, user2_id, guild_id):
    try:
        supabase.table("pairings").insert({"user1_id": str(user1_id), "user2_id": str(user2_id), "guild_id": str(guild_id), "active": True}).execute()
    except Exception as e: print(f"Error starting pair: {e}")

def end_pairing(user1_id, user2_id, guild_id):
    try:
        now = datetime.now(timezone.utc).isoformat()
        res = supabase.table("pairings").select("*").eq("guild_id", str(guild_id)).eq("active", True).execute()
        for p in res.data:
            if (p['user1_id'] == str(user1_id) and p['user2_id'] == str(user2_id)) or (p['user1_id'] == str(user2_id) and p['user2_id'] == str(user1_id)):
                supabase.table("pairings").update({"active": False, "end_time": now}).eq("id", p['id']).execute()
    except Exception as e: print(f"Error ending pair: {e}")

def get_active_pairs(guild_id):
    try:
        return supabase.table("pairings").select("*").eq("guild_id", str(guild_id)).eq("active", True).execute().data
    except Exception as e: return []

def get_user_pairing(user_id, guild_id):
    try:
        res = supabase.table("pairings").select("*").eq("guild_id", str(guild_id)).eq("active", True).execute()
        for p in res.data:
            if p['user1_id'] == str(user_id) or p['user2_id'] == str(user_id): return p
        return None
    except Exception as e: return None

def get_user_history(user_id, guild_id):
    try:
        res = supabase.table("pairings").select("*").eq("guild_id", str(guild_id)).execute()
        history = []
        for p in res.data:
            if p['user1_id'] == str(user_id) or p['user2_id'] == str(user_id):
                history.append(p)
        return history
    except Exception as e: return []

def get_total_users_count(guild_id):
    try:
        response = supabase.table("users").select("user_id").eq("guild_id", str(guild_id)).execute()
        return len(response.data) if response.data else 0
    except Exception as e:
        print(f"Users Count Error: {e}")
        return 0

def get_active_pairs_count(guild_id):
    try:
        pairs = get_active_pairs(guild_id)
        return len(pairs) if pairs else 0
    except Exception as e:
        print(f"Pairs Count Error: {e}")
        return 0

def get_total_swipes_count(guild_id):
    try:
        response = supabase.table("swipes").select("id").eq("guild_id", str(guild_id)).execute()
        return len(response.data) if response.data else 0
    except Exception as e:
        print(f"Swipes Count Error: {e}")
        return 0