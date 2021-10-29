import discord, os, json, requests
from discord.ext import commands
import datetime
import stats as statistics, math
from discord.ext.commands import MemberConverter
import setup

def ratioFunction(x, y, z):
    return f"{round(x/(x+y+z), 2)} : {round(y/(x+y+z), 2)} : {round(z/(x+y+z), 2)}"

def generate_time(timeSeconds):
    day = timeSeconds // (24 * 3600);timeSeconds = timeSeconds % (24 * 3600);hour = timeSeconds // 3600;timeSeconds %= 3600;minutes = timeSeconds // 60;timeSeconds %= 60;seconds = timeSeconds

    day = f" {round(day)}d" if day != 0 else ""
    hour = f" {round(hour)}h" if hour != 0 else ""
    minutes = f" {round(minutes)}m" if minutes != 0 else ""

    if day == "" and hour == "" and minutes == "":
        return f"{round(seconds)}s"
    
    return f"{day}{hour}{minutes}".lstrip()

secret = setup.spotifySecret
id = setup.spotifyId

class cmds(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="reload")
    async def reload(self, ctx):

        if ctx.author.id == 368071242189897728:
            blacklisted_ids = setup.blacklisted_ids

            data = statistics.getDefaultData(blacklisted_ids)

            statistics.saveData(data)

            return await ctx.send(f"Reloaded mainfile to: ```json\n{json.dumps(data)}\n```")
        else:
            return await ctx.send("nice try")

    @commands.command(name="spotify")
    async def spotify(self, ctx, member = None, user = None):

        section = "all time"
        directory = statistics.directory + "all.json"
        if member:
            if member.lower() in ["day", "today", "24h"]:
                section = "today"
                directory = statistics.directory + "day.json"
                member = None
            elif member.lower() == "week":
                section = "this week"
                directory = statistics.directory + "week.json"
                member = None
            elif member.lower() == "month":
                section = "this month"
                directory = statistics.directory + "month.json"
                member = None
            else:
                section = "all time"
                directory = statistics.directory + "all.json"
                converter = MemberConverter()

                if user != None:
                    member = member + " " + user

                member = await converter.convert(ctx, member)
        
        if user != None:
            converter = MemberConverter()
            member = await converter.convert(ctx, user)
        
        if member == None:
            member = ctx.author

        stats = statistics.Stats(location=directory)
        user = stats.users[str(member.id)]

        if user.spotify == {}:
            return await ctx.send("> This user has never shown spotify on their status!")

        auth = statistics.spotify.Auth(id, secret)
        user.getSpotifyStats(auth)

        avg = "_ _ "
        spotifyExtension = "_ _ "
        spotifyExtensionArtists = "_ _ "

        songs = user.spotifyStats.songList
        artists = user.spotifyStats.artists

        for feature in user.spotifyStats.averageFeatures.supportedTypes:
            if feature in ["tempo"]:
                continue
            avg += f"{feature.title()} - **{round(getattr(user.spotifyStats.averageFeatures, feature) * 100)}%**\n"
        
        counter = 0
        for song in songs:
            counter += 1
            if counter <= 10:
                spotifyExtension = spotifyExtension + f"{counter}. **{math.floor(song.duration.total_seconds() / 60)}:{str(round(song.duration.total_seconds()%60)).zfill(2)}** {', '.join([artist.name for artist in song.artists])} - {song.name}  (`{generate_time(user.spotify[song.id].totalTime.total_seconds())}`)\n"
        
        counter = 0
        for artistName, artistLength in artists.items():
            counter += 1
            if counter <= 10:
                spotifyExtensionArtists += f"{counter}. **{artistLength[0].followers:,d}** [{artistLength[0].name}]({artistLength[0].url}) (`{generate_time(artistLength[1].total_seconds())}`)\n"

        embed = discord.Embed(title=f"Summary of {member.name}'s spotify listening ({section.title()})", description="() -> Total time\n[] -> Last seen", color=0xFFFF00)
        embed.add_field(name="Average Tempo (BPM)", value=str(round(user.spotifyStats.averageFeatures.tempo)))
        embed.add_field(name="Average Song Popularity", value=str(round(user.spotifyStats.averagePopularity)) + "*")
        embed.add_field(name="Average Song Length", value=f"{math.floor(user.spotifyStats.averageLength.total_seconds() / 60)}:{str(round(user.spotifyStats.averageLength.total_seconds()%60)).zfill(2)}")
        embed.add_field(name="Average Song Features", value=avg, inline=False)
        embed.add_field(name="Top Songs Listened To", value=spotifyExtension, inline=False)
        embed.add_field(name="Top Artists Listened To", value=spotifyExtensionArtists, inline=False)

        embed.set_footer(text="*Song popularity is a number based on plays and song release date. More recent and more played songs have a higher popularity number.")

        await ctx.send(embed=embed)

        
        

    @commands.command(name="roundup", aliases=["summary"])
    async def roundup(self, ctx, member = None, *, user = None):
        
        section = "all time"
        directory = statistics.directory + "all.json"
        if member:
            if member.lower() in ["day", "today", "24h"]:
                section = "today"
                directory = statistics.directory + "day.json"
                member = None
            elif member.lower() == "week":
                section = "this week"
                directory = statistics.directory + "week.json"
                member = None
            elif member.lower() == "month":
                section = "this month"
                directory = statistics.directory + "month.json"
                member = None
            else:
                section = "all time"
                directory = statistics.directory + "all.json"
                converter = MemberConverter()

                if user != None:
                    member = member + " " + user

                member = await converter.convert(ctx, member)
        
        if user != None:
            converter = MemberConverter()
            member = await converter.convert(ctx, user)

        stats = statistics.Stats(location=directory)

        if member != None:

            if str(member.id) in stats.users:
                user = stats.users[str(member.id)]
            else:
                return await ctx.send("Couldnt find user f")

            allGames = "_ _ "
            counter = 0
            for activityName, activity in user.activities.items():
                counter += 1
                if counter <= 10:
                    allGames = allGames + f"{counter}. {activityName} - (`{generate_time(activity.totalTime.total_seconds())}`) - [{activity.lastSeen.timestamp.relative}]\n"
            
            allCustomStatuses = "_ _ "
            counter = 0
            for statusName, customStatus in user.statuses.items():
                counter += 1
                if counter <= 10:
                    allCustomStatuses = allCustomStatuses + f"{counter}. {statusName} - (`{generate_time(customStatus.totalTime.total_seconds())}`) - [{customStatus.lastSeen.timestamp.relative}]\n"

            voiceExtension = "_ _ "
            counter = 0
            for channelId, voiceData in user.voice.items():
                counter += 1
                if counter <= 10:
                    voiceExtension = voiceExtension + f"{counter}. <#{channelId}> (`{generate_time(voiceData.totalTime.total_seconds())}`) [{voiceData.lastSeen.timestamp.relative}]\n"

            allStatuses = f"""
Online {f"(`{generate_time(user.types.online.totalTime.total_seconds()) if user.types.online else '0s'}`) - [{user.types.online.lastSeen.timestamp.relative}]" if user.types.online else "(`0s`)"}
Idle {f"(`{generate_time(user.types.idle.totalTime.total_seconds()) if user.types.idle else '0s'}`) - [{user.types.idle.lastSeen.timestamp.relative}]" if user.types.idle else "(`0s`)"}
Do Not Disturb {f"(`{generate_time(user.types.dnd.totalTime.total_seconds()) if user.types.dnd else '0s'}`) - [{user.types.dnd.lastSeen.timestamp.relative}]" if user.types.dnd else "(`0s`)"}
Offline {f"(`{generate_time(user.types.offline.totalTime.total_seconds()) if user.types.offline else '0s'}`) - [{user.types.offline.lastSeen.timestamp.relative}]" if user.types.offline else "(`0s`)"}
            """

            allPlatforms = "_ _ "
            for platformName, platform in user.platforms.items():
                allPlatforms += f"{platform.name} (`{generate_time(platform.totalTime.total_seconds())}`) {f'- [{platform.lastSeen.timestamp.relative}]' if platform.lastSeen != None else ''}\n"

            more = f"""
Total Tracked Time: `{generate_time(stats.more.totalTracked.total_seconds())}`
Total Online Time (user): `{generate_time(user.more.totalOnline.total_seconds())}`
Online : Idle : Offline ratio: `{user.more.onlineRatio}`
            """
            
            embed = discord.Embed(title=f"Summary of {member.name}'s games ({section.title()})", description="() -> Total time\n[] -> Last seen", color=0xFFFF00)

            if user.spotify != {}:
                embed.set_footer(text=f"See more Spotify statistics for this user with 's!spotify {member.name}'")

            embed.add_field(name="All Games Together", value=allGames, inline=False)
            embed.add_field(name="All Statuses", value=allStatuses, inline=False)
            embed.add_field(name="Custom Statuses", value=allCustomStatuses, inline=False)
            embed.add_field(name="Extensions - Voice", value=voiceExtension, inline=False)
            embed.add_field(name="Extensions - Platforms", value=allPlatforms, inline=False)
            embed.add_field(name="Extensions - Messages Sent", value=user.messages, inline=False)
            embed.add_field(name="More", value=more, inline=False)

            if directory == statistics.directory + "all.json":
                embed.add_field(name="Top Tip!", value="Use `s!summary [day/week/month] *[user/game]` to get anayltics for a certain time frame", inline=False)

            await ctx.send(embed=embed)


        else:

            allTotals = "_ _ "
            userStatuses = "_ _ "

            counter = 0
            for activityName, activity in stats.activities.items():
                counter += 1
                if counter > 10:
                    continue
                allTotals += f"{counter}. {activityName} - `{generate_time(activity.totalTime.total_seconds())}` (<@{list(activity.topUsers)[0]}> - {generate_time(activity.topUsers[list(activity.topUsers)[0]].activities[activityName].totalTime.total_seconds())})\n"

            counter = 0
            for userid, user in stats.users.items():
                counter += 1
                if counter > 10:
                    continue
                userStatuses += f"{counter}. <@{userid}>: Total Online (`{generate_time(user.more.totalOnline.total_seconds())}`) [{user.more.lastOnline.timestamp.relative if user.more.lastOnline else 'Never'}]" + "\n"

            more = f"""
Total Online Time: `{generate_time(stats.more.totalOnline.total_seconds())}`
Average Online Time: `{generate_time(stats.more.averageOnline.total_seconds())}`
Total Tracked Time: `{generate_time(stats.more.totalTracked.total_seconds())}`
            """

            embed = discord.Embed(title=f"Summary of everyone's games ({section.title()})", description="() = Highest user", color=0xFFFF00)
            embed.add_field(name="All Games Together", value=allTotals, inline=False)
            embed.add_field(name="All Statuses", value=userStatuses, inline=False)
            embed.add_field(name="Extensions - Messages Sent", value=stats.more.totalMessages, inline=False)
            embed.add_field(name="More", value=more, inline=False)
            
            if directory == statistics.directory + "all.json":
                embed.add_field(name="Top Tip!", value="Use `s!summary [day/week/month] *[user/game]` to get anayltics for a certain time frame", inline=False)

            await ctx.send(embed=embed)
    
    @roundup.error
    async def do_repeat_handler(self, ctx, error):

        

        if not isinstance(error, commands.MemberNotFound):
            raise error
        
        
        
        if len(ctx.message.content.split(" ")) > 1:
            arg = ctx.message.content.split(" ")[1]

            if arg.lower() in ["day", "today", "24h"]:
                section = "today"
                directory = statistics.directory + "day.json"
            elif arg.lower() == "week":
                section = "this week"
                directory = statistics.directory + "week.json"
            elif arg.lower() == "month":
                section = "this month"
                directory = statistics.directory + "month.json"
            else:
                section = "all time"
                directory = statistics.directory + "all.json"
        
        stats = statistics.Stats(location=directory)

        arg = str(error).split("\"")[1].lower()

        activites = {key.lower():value for key, value in stats.activities.items()}

        if arg not in activites:
            return await ctx.send("Could not find user or activity!")
        
        activity = activites[arg]
        activityName = activity.name

        playtime = "_ _ "

        for userID, user in activity.topUsers.items():
            playtime += f"<@{userID}> - `{generate_time(user.activities[activityName].totalTime.total_seconds())}` [{user.activities[activityName].lastSeen.timestamp.relative}]\n"
        
        more = f"""
Total time on this game: `{generate_time(activity.more.totalPlayed.total_seconds())}`
Average time on this game: `{generate_time(activity.more.averagePlayed.total_seconds())}`
Total tracked time: `{generate_time(stats.more.totalTracked.total_seconds())}`
        """


        embed = discord.Embed(title=f"Summary of {arg.title()} ({section.title()})", description="_ _", color=0xFFFF00)
        embed.add_field(name="Playtime", value=playtime, inline=False)
        embed.add_field(name="More", value=more, inline=False)

        if directory == statistics.directory + "all.json":
                embed.add_field(name="Top Tip!", value="Use `s!summary [day/week/month] *[user/game]` to get anayltics for a certain time frame", inline=False)

        await ctx.send(embed=embed)



    @commands.command(name="activity", aliases=["activities", "game", "games"])
    async def activity(self, ctx):
        activities = self.bot.get_guild(691570617387843635).get_member(519206205512744972).activities
        finalactivities = "_ _ "
        for activity in activities:
            try:
                seconds = (datetime.datetime.now() - activity.start).total_seconds()
                m, s = divmod(seconds, 60)
                h, m = divmod(m, 60)
                finalactivities = finalactivities + f"{activity.name} (`" + '{:d}H, {:02d}M, {:02d}S'.format(round(h), round(m), round(s)) + "`)\n"
            except:
                pass
        embed = discord.Embed(title="Grog activities", description=finalactivities, color=0x00ff00)
        try:
            await ctx.send(embed=embed)
        except:
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(cmds(bot))