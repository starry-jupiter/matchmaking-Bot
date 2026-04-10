import os
import json
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyze_intro(user_intro):
    prompt = f"""
    Analyze this Discord matchmaking intro. 
    Convert all "Small Caps" (ɴᴀᴍᴇ -> Name) to standard text.
    
    1. Identify the user's gender: "man", "woman", or "non-binary".
    2. Determine who they are looking to date/match with.
    3. Map their "Looking For" preference to a list: ["man"], ["woman"], ["non-binary"], or multiple.
    4. Extract likes and dislikes as lists.
    5. Convert Timezone (like EST) to a GMT offset number (EST = -5).
    
    CRITICAL NORMALIZATION RULE:
    When extracting 'likes', 'dislikes', and any interests, you MUST normalize the terminology into broad, standard categories. Do not use the user's exact slang. 
    - "gaming", "ps5", "pc" -> "Video Games"
    - "gym", "lifting" -> "Fitness & Gym"
    - Apply this logic to all hobbies. Capitalize the first letter of each word.

    🚨 CRITICAL TOXICITY & SAFETY CHECK 🚨
    You are a safety moderator. Analyze the text for:
    - NSFW, sexual, or creepy content.
    - Extreme toxicity, slurs, or harassment.
    
    NOTE: Users aged 13-17 ARE allowed and are not "bypassing restrictions" 
    simply by stating their age. Only flag as toxic if they are being 
    inappropriate, sexual, or explicitly trying to hide their age.
    
    If any violation is found, set "is_toxic" to true. Otherwise, false.

    Return ONLY a JSON object exactly like this:
    {{
      "name": "string",
      "age": int,
      "gender": "man" or "woman" or "non-binary",
      "attracted_to": ["woman"], 
      "prns": "string",
      "gmt": int,
      "likes": ["Video Games"],
      "dislikes": ["Dry Texting"],
      "extra": "string",
      "is_toxic": false,
      "toxic_reason": null
    }}

    Intro Text:
    "{user_intro}"
    """
    try:
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant", # Updated to a supported model
            response_format={"type": "json_object"}
        )
        return json.loads(chat.choices[0].message.content)
    except Exception as e:
        print(f"Error analyzing intro: {e}")
        return {"is_toxic": True, "toxic_reason": f"Crash Reason: {str(e)}"}

def generate_icebreaker(likes1, likes2):
    prompt = f"""
    You are a friendly AI matchmaker. 
    User 1 likes: {likes1}
    User 2 likes: {likes2}
    
    Write a fun, casual 1-sentence icebreaker to get them talking. 
    Mention a shared interest if they have one, otherwise ask a fun either/or question based on their differing interests.
    """
    try:
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant", # Updated to a supported model
            temperature=0.7,
            max_tokens=100
        )
        return chat.choices[0].message.content.replace('"', '').strip()
    except Exception as e:
        print(f"Error generating icebreaker: {e}")
        return "You both have awesome profiles! Why not start by sharing your favorite hobby?"