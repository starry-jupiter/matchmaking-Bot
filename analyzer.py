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
    
    🚨 CRITICAL AGE RULE 🚨
    Extract their CURRENT age as an integer. If they say "15 turning 16", "almost 18", or "17 but turning 18 soon", you MUST extract their CURRENT age (15, 17). Ignore the future age entirely!

    🚨 CRITICAL TOXICITY & SAFETY CHECK 🚨
    You are a lenient but vigilant safety moderator. Give users the benefit of the doubt for casual text, but strictly enforce severe violations.
    
    DEFINITELY FLAG FOR (Set "is_toxic" to true):
    - Severe NSFW, explicit sexual requests, or adult content.
    - Hate speech, racial/homophobic slurs, or discriminatory language.
    - Predatory, creepy, or grooming behavior.
    - Threats of violence, severe harassment, or doxing.
    - Adults (18+) explicitly trying to date or match with minors (under 18).
    
    DO NOT FLAG FOR (Set "is_toxic" to false):
    - Slang, jokes, sarcasm, or casual swearing (e.g., "lmao", "wtf", "af").
    - Emotional expressions or "dramatic" emojis (e.g., 😭, 💀, 🥺, 💔).
    - Being "overly dramatic" or using excessive punctuation (e.g., "I will literally die if...", "plzzzzz").
    - Users aged 13-17 stating their age normally.
    
    If a severe violation is found from the "DEFINITELY FLAG FOR" list, set "is_toxic" to true and state the exact reason in "toxic_reason". Otherwise, set "is_toxic" to false. But use your best judgement if it's not on the list better to be safe then sorry.
    
    Give users the benefit of the doubt. If it is just someone being dramatic, using slang, or typing casually, let it pass. 
    
    If any SEVERE violation is found, set "is_toxic" to true and state the exact severe reason. Otherwise, false.

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
    Mention a shared interest if they have one, otherwise ask a fun either/or question based on their differing interests. Do not include the prompt in your response only the icebreaker. Keep it light and engaging!
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