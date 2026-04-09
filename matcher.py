def calculate_match_score(user1_profile, user2_profile):
    score = 0
    
    # Check for overlapping interests
    shared_interests = set(user1_profile['interests']) & set(user2_profile['interests'])
    score += len(shared_interests) * 20  # 20 points per shared hobby
    
    # Vibe check (Simple logic: if any vibe words match)
    if any(vibe in user2_profile['vibe'] for vibe in user1_profile['vibe']):
        score += 30
        
    return score

# Example usage
user1 = {"vibe": "nerdy, creative, chill", "interests": ["robots", "hiking"]}
user2 = {"vibe": "techy, active, curious", "interests": ["robots", "cooking"]}

print(f"Match Score: {calculate_match_score(user1, user2)}%")