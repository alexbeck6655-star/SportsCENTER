print("✅ SportsCENTER is working!")
print("Here is a fake odds snapshot just to prove output works:")

# Fake example data for testing
games = [
    {"matchup": "Jets vs Patriots", "player": "Breece Hall", "odds": "+120"},
    {"matchup": "Eagles vs Cowboys", "player": "A.J. Brown", "odds": "-105"},
]

for game in games:
    print(f"{game['matchup']} | {game['player']} Anytime TD: {game['odds']}")

print("✅ Test finished successfully.")
