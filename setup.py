import os 

#Token for the discord bot
botToken = os.getenv("botToken")

# Database token (if your database is setup this way)
databaseToken = os.getenv("databaseToken")

# Spotify API ID - SPOTIFY COMMANDS WONT WORK WITHOUT THIS
spotifyId = os.getenv("spotifyId")

# Spotify API Secret - SPOTIFY COMMANDS WONT WORK WITHOUT THIS
spotifySecret = os.getenv("spotifySecret")

# IDs for the bot to ignore
blacklisted_ids = []

# Guild ID for the bot to track users in (only supports one guild currently)
searchGuild = 0

# Prefixes for the bot to listen for 
prefixes = ["stats ", "status ", "s!", "Stats ", "Status ", "S!"]

