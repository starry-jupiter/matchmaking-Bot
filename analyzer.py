def analyze_intro(user_intro):
    prompt = f"""
    Analyze this Discord matchmaking intro. 
    Convert all "Small Caps" (ɴᴀᴍᴇ -> Name) to standard text.
    
    1. Identify the user's gender: Map it strictly to "man", "woman", or "non-binary". 
       - "man" includes: cis man, trans man, transmasc, male, boy.
       - "woman" includes: cis woman, trans woman, transfem, female, girl.
       - "non-binary" includes: enby, genderfluid, agender, bigender, genderqueer, demiboy, demigirl, gender non-conforming, two-spirit, neutrois.
       - 🚨 IF they put a sexuality or a birth assignment (like AFAB, AMAB, AGAB) in the gender field, look at their pronouns to figure out their actual gender! ("she/her" = "woman", "he/him" = "man", "they/them" or mixed like "she/they" = "non-binary").
    
    2. Extract their sexuality or who they are looking to date.
    
    3. Map their "Looking For" preference to a list using EXACTLY these terms: "man", "woman", "non-binary", or "any". They can have multiple!
       - "lesbian", "sapphic", "straight man", "heterosexual man", "gynephilic" -> ["woman"]
       - "gay", "gay man", "achillean", "vincian", "straight woman", "heterosexual woman", "androphilic" -> ["man"]
       - "bisexual" or "bi" -> ["man", "woman"]
       - "pansexual", "omnisexual", "polysexual", "pan", "omni", "fluid", "queer", "anyone", "any", "don't care", "all" -> ["any"]
       - "neptunic" (attracted to women and non-binary) -> ["woman", "non-binary"]
       - "uranic" (attracted to men and non-binary) -> ["man", "non-binary"]
       - "trixic" (non-binary attracted to women) -> ["woman"]
       - "toric" (non-binary attracted to men) -> ["man"]
       - "diamoric" or "enbian" (non-binary attracted to non-binary) -> ["non-binary"]
       - "skoliosexual" or "ceterosexual" (attracted exclusively to non-binary people) -> ["non-binary"]
       
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
            model="llama-3.1-8b-instant",
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
    
    TASK: Write a fun, casual 1-sentence icebreaker to get them talking. 
    - Mention a shared interest if they have one.
    - If no shared interests exist, ask a fun either/or question based on their differing interests.
    
    STRICT CONSTRAINT: 
    - Output ONLY the icebreaker text itself. 
    - DO NOT include introductory phrases (e.g., "Here is your icebreaker").
    - DO NOT include meta-commentary about the interests or why you chose the question.
    - DO NOT use quotation marks around the final response.
    """
    try:
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=100
        )
        # Clean up any accidental leading/trailing whitespace or quotes
        return chat.choices[0].message.content.replace('"', '').strip()
    except Exception as e:
        print(f"Error generating icebreaker: {e}")
        return "You both have awesome profiles! Why not start by sharing your favorite hobby?"