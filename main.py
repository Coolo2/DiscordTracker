import discord, os, json, requests
from discord.ext import commands, tasks
import datetime
from webserver import keep_alive
import stats as statistics
import setup

intents = discord.Intents().all()

bot = commands.Bot(command_prefix=setup.prefixes, intents=intents, case_insensitive=True)

blacklisted_ids = setup.blacklisted_ids
searchGuild = setup.searchGuild

lastMessages = {}

@bot.event
async def on_ready():
    print("up")
    await check.start()

@bot.event 
async def on_message(message):
    await bot.process_commands(message)
    guild = bot.get_guild(searchGuild)

    for member in guild.members:
        if member.id == message.author.id:

            if str(member.id) not in lastMessages:
                lastMessages[str(member.id)] = 0
            
            lastMessages[str(member.id)] += 1

global prevactivities
prevactivities = {}

waitTime = 20

async def save_data( lastMessages, guild : discord.Guild, location=statistics.directory + "all.json"):
    data = statistics.getData(location)

    data = reloadTimeframe(location)

    for member in guild.members:
        if member.bot == True or str(member.id) in data["ids"]:
            continue

        if str(member.id) not in data["users"]:
            data["users"][str(member.id)] = {}
        if str(member.id) not in prevactivities:
            prevactivities[str(member.id)] = ()

        if "activities" not in data["users"][str(member.id)]:
            data["users"][str(member.id)] = {
                "activities":{},
                "statuses":{},
                "types":{},
                "extensions":{}
            }
        if str(member.status) not in data["users"][str(member.id)]["types"]:
            data["users"][str(member.id)]["types"][str(member.status)] = {"total_time":0}

        if "platforms" not in data["users"][str(member.id)]["extensions"]:
            data["users"][str(member.id)]["extensions"]["platforms"] = {
                "desktop":{},
                "mobile":{},
                "web":{}
            }
        statuses = {"desktop":member.desktop_status, "mobile":member.mobile_status, "web":member.web_status}
        for platform in statuses:
            if str(statuses[platform]) in ["online", "idle", "dnd"]:
                if "total_time" not in data["users"][str(member.id)]["extensions"]["platforms"][platform]:
                    data["users"][str(member.id)]["extensions"]["platforms"][platform]["total_time"] = 0
                data["users"][str(member.id)]["extensions"]["platforms"][platform]["total_time"] += waitTime
                data["users"][str(member.id)]["extensions"]["platforms"][platform]["last_seen"] = datetime.datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)")
        
        if "messages" not in data["users"][str(member.id)]["extensions"]:
            data["users"][str(member.id)]["extensions"]["messages"] = 0
        
        if str(member.id) in lastMessages:
            data["users"][str(member.id)]["extensions"]["messages"] += lastMessages[str(member.id)]
        
        for activity in member.activities:

            if isinstance(activity, discord.Spotify):
                if "spotify" not in data["users"][str(member.id)]["extensions"]:
                    data["users"][str(member.id)]["extensions"]["spotify"] = {}
                spotify = data["users"][str(member.id)]["extensions"]["spotify"]

                if activity.track_id not in spotify or type(spotify[activity.track_id]) == dict:
                    spotify[activity.track_id] = 0  

                spotify[activity.track_id] += waitTime

            try:
                activity.start
                if str(activity.name) not in data["users"][str(member.id)]["activities"]:
                    data["users"][str(member.id)]["activities"][str(activity.name)] = {}
                if "total_time" not in data["users"][str(member.id)]["activities"][str(activity.name)]:
                    data["users"][str(member.id)]["activities"][str(activity.name)]["total_time"] = 0
                if "online_time" not in data["users"][str(member.id)]["activities"][str(activity.name)]:
                    data["users"][str(member.id)]["activities"][str(activity.name)]["online_time"] = 0

                if str(member.status) != "idle":
                    data["users"][str(member.id)]["activities"][str(activity.name)]["online_time"] += waitTime
                data["users"][str(member.id)]["activities"][str(activity.name)]["total_time"] += waitTime
                data["users"][str(member.id)]["activities"][str(activity.name)]["last_seen"] = datetime.datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)")
            except:
                if str(activity.name) not in data["users"][str(member.id)]["statuses"]:
                    data["users"][str(member.id)]["statuses"][str(activity.name)] = {"total_time":0}
                data["users"][str(member.id)]["statuses"][str(activity.name)]["total_time"] += waitTime
                data["users"][str(member.id)]["statuses"][str(activity.name)]["last_seen"] = datetime.datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)")
        
        data["users"][str(member.id)]["types"][str(member.status)]["total_time"] += waitTime
        data["users"][str(member.id)]["types"][str(member.status)]["last_seen"] = datetime.datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)")
    
    for guild in bot.guilds:
        for channel in guild.channels:
            if channel.type == discord.ChannelType.voice:
                for member in channel.members:
                    if str(member.id) in data["users"]:
                        if "voice" not in data["users"][str(member.id)]["extensions"]:
                            data["users"][str(member.id)]["extensions"]["voice"] = {}
                        
                        voice = data["users"][str(member.id)]["extensions"]["voice"]

                        if str(member.voice.channel.id) not in voice:
                            voice[str(member.voice.channel.id)] = {}

                        if "total_time" not in voice[str(member.voice.channel.id)]:
                            voice[str(member.voice.channel.id)]["total_time"] = 0
                        
                        voice[str(member.voice.channel.id)]["total_time"] += waitTime
                        voice[str(member.voice.channel.id)]["last_seen"] = datetime.datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)")
    
    statistics.saveData(data, location)

def reloadTimeframe(location):

    dtToday = datetime.datetime.today()
    day = f"{dtToday.year}/{dtToday.month}/{dtToday.day}"

    data = statistics.getData(location)

    if location == statistics.directory + "day.json":

        if data["lastReloaded"] != day:
            data = statistics.getDefaultData(blacklisted_ids) 
    
    elif location == statistics.directory + "week.json":

        lastReloaded = datetime.datetime.strptime(data["lastReloaded"], '%Y/%m/%d')

        if (dtToday - datetime.timedelta(days=7)) > lastReloaded:
            data = statistics.getDefaultData(blacklisted_ids)  
    
    elif location == statistics.directory + "month.json":

        lastReloaded = datetime.datetime.strptime(data["lastReloaded"], '%Y/%m/%d')

        if (dtToday - datetime.timedelta(days=28)) > lastReloaded:
            data = statistics.getDefaultData(blacklisted_ids)  

    return data




@tasks.loop(seconds=waitTime)
async def check():
    
    global prevactivities
    global lastMessages

    guild = bot.get_guild(searchGuild)

    await save_data(lastMessages, guild, statistics.directory + "day.json")
    await save_data(lastMessages, guild, statistics.directory + "week.json")
    await save_data(lastMessages, guild, statistics.directory + "month.json")

    await save_data(lastMessages, guild, statistics.directory + "all.json")

    lastMessages = {}


keep_alive()


if __name__ == "__main__":  
    try:
        bot.load_extension("cog")
        print("loaded")
    except Exception as e:
        print(e)
    bot.run(setup.botToken)