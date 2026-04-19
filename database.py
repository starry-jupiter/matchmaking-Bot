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

def get_strict_matches(user_id, guild_id):
    # 1. Fetch the swiper's profile
    me_res = supabase.table("profiles").select("*").eq("user_id", str(user_id)).eq("guild_id", str(guild_id)).execute()
    if not me_res.data: return []
    me = me_res.data[0]
    my_age = int(me['age'])
    
    # --- FIX 1: Fetch swiped history to prevent repeats ---
    swipes_res = supabase.table("swipes").select("target_id").eq("user_id", str(user_id)).eq("guild_id", str(guild_id)).execute()
    swiped_ids = set(str(s['target_id']) for s in swipes_res.data) if swipes_res.data else set()
    
    # 2. Fetch all other profiles in the server
    others = supabase.table("profiles").select("*").eq("guild_id", str(guild_id)).neq("user_id", str(user_id)).execute().data
    
    matches = []
    for p in others:
        # --- FIX 2: Skip profiles you have already swiped on ---
        if str(p['user_id']) in swiped_ids:
            continue

        their_age = int(p['age'])
        
        # --- AGE GAP LOGIC (Kept for safety) ---
        allowed = False
        if my_age == 13:
            if their_age in [13, 14]: allowed = True
        elif 14 <= my_age <= 17:
            if abs(my_age - their_age) <= 2: allowed = True
        elif my_age == 18:
            if their_age >= 16: allowed = True
        elif my_age >= 19:
            if their_age >= 19 and abs(my_age - their_age) <= 5: allowed = True

        if not allowed: continue
        
        # --- GENDER & ATTRACTION CHECK (Kept for compatibility) ---
        they_like_me = "any" in p['attracted_to'] or me['gender'] in p['attracted_to']
        i_like_them = "any" in me['attracted_to'] or p['gender'] in me['attracted_to']

        if not (they_like_me and i_like_them):
            continue

        # --- FIX 3: Removed all Likes, Dislikes, and Interest filters ---
        # Profiles are now added as long as they pass Age and Gender checks
        matches.append(p)
            
    return matches
    
    # 2. Fetch all other profiles in the server
    others = supabase.table("profiles").select("*").eq("guild_id", str(guild_id)).neq("user_id", str(user_id)).execute().data
    
    matches = []
    for p in others:
        their_age = int(p['age'])
        
        # --- NEW STRICT AGE GAP LOGIC ---
        allowed = False
        
        # Rule: 13 year olds can only see 13 and 14
        if my_age == 13:
            if their_age in [13, 14]: allowed = True
            
        # Rule: 14-17 year olds can see 2 years up or down
        elif 14 <= my_age <= 17:
            if abs(my_age - their_age) <= 2: allowed = True
            
        # Rule: 18 year olds can see 16+ (anyone over)
        elif my_age == 18:
            if their_age >= 16: allowed = True
            
        # Rule: 19+ has a 5 year limit (19+ anyone over but within 5 years)
        elif my_age >= 19:
            if their_age >= 19 and abs(my_age - their_age) <= 5: allowed = True

        if not allowed: continue
        
        # --- GENDER & ATTRACTION CHECK ---
        if me['gender'] not in p['attracted_to'] or p['gender'] not in me['attracted_to']: 
            continue

        # --- LIKES/DISLIKES FILTER ---
        my_l = set(x.lower() for x in (me.get('likes') or []))
        my_d = set(x.lower() for x in (me.get('dislikes') or []))
        th_l = set(x.lower() for x in (p.get('likes') or []))
        th_d = set(x.lower() for x in (p.get('dislikes') or []))

        # Hard Filter: Do not show if a 'Like' hits a 'Dislike'
        if my_l.intersection(th_d) or th_l.intersection(my_d): 
            continue
        # Priority: Must share at least one interest to show up
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