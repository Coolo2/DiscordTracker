import datetime, json, requests, os
import spotify
import setup

directory = "tracker/"

def ratioFunction(x, y, z):
    return f"{round(x/(x+y+z), 2)} : {round(y/(x+y+z), 2)} : {round(z/(x+y+z), 2)}"

class LastSeen():

    class Timestamp():

        def __init__(self, time : datetime.datetime):

            self.integer = round(time.timestamp())
            self.relative = f"<t:{self.integer}:R>"

            self.relative = "Now" if (datetime.datetime.now() - time).total_seconds() < 21 else self.relative

    def __init__(self, data : str):

        self.time = None 
        self.string = ""
        self.timestamp = None

        self.loadData(data)

    def loadData(self, data):
        self.time = datetime.datetime.strptime(data, '%d-%b-%Y (%H:%M:%S.%f)')
        self.string = data 
        self.timestamp = self.Timestamp(self.time)

class Activity():

    def __init__(self, name, data):
        

        self.name = name
        self.totalTime = 0
        self.onlineTime = 0
        self.lastSeen = 0
        

        self.loadData(data)


    def loadData(self, data):
        self.data = data

        self.totalTime = datetime.timedelta(seconds=data["total_time"])
        self.onlineTime = datetime.timedelta(seconds=data["online_time"])
        self.lastSeen = LastSeen(data["last_seen"])

class ListActivity():

    class MoreStats():

        def __init__(self, statData):

            self.totalPlayed = datetime.timedelta(seconds=0)
            self.averagePlayed = datetime.timedelta(seconds=0)

        

    def __init__(self, name):
        
        self.name = name
        self.totalTime = datetime.timedelta(seconds=0)
        self.topUsers = {}
        self.more = self.MoreStats(self)


    def addUser(self, user):

        self.totalTime += user.activities[self.name].totalTime
        self.topUsers[str(user.id)] = user

        self.topUsers = dict(sorted(self.topUsers.items(), key=lambda item: item[1].activities[self.name].totalTime, reverse=True))

        self.more.totalPlayed += user.activities[self.name].totalTime

        self.more.averagePlayed = datetime.timedelta(seconds=self.more.totalPlayed.total_seconds() / len(self.topUsers))



class Status():

    def __init__(self, name, data):
        

        self.name = name
        self.totalTime = 0
        self.lastSeen = 0

        self.loadData(data)


    def loadData(self, data):
        self.data = data

        self.totalTime = datetime.timedelta(seconds=data["total_time"])
        self.lastSeen = LastSeen(data["last_seen"])
        
class Types():

    class Type():

        def __init__(self, name, data):

            self.name = name
            self.totalTime = 0
            self.lastSeen = 0

            self.loadData(data)


        def loadData(self, data):
            self.data = data

            self.totalTime = datetime.timedelta(seconds=data["total_time"])
            self.lastSeen = LastSeen(data["last_seen"])

    def __init__(self, data):

        self.online = None
        self.idle = None
        self.dnd = None
        self.offline = None

        self.all = {}

        self.loadData(data)
    
    def loadData(self, data):
        self.data = data  

        types = {
            "online": self.online,
            "idle": self.idle, 
            "dnd": self.dnd,
            "offline": self.offline
        }
        if "online" in data and data["online"]["total_time"] != 0:
            self.online = self.Type("online", data["online"])
        if "idle" in data and data["idle"]["total_time"] != 0:
            self.idle = self.Type("idle", data["idle"])
        if "dnd" in data and data["dnd"]["total_time"] != 0:
            self.dnd = self.Type("dnd", data["dnd"])
        if "offline" in data and data["offline"]["total_time"] != 0:
            self.offline = self.Type("offline", data["offline"])

        for statusType in types:
            if statusType in data:
                
                self.all[statusType] = self.Type(statusType, data[statusType])
        
        self.all = dict(sorted(self.all.items(), key=lambda item: item[1].totalTime, reverse=True))

class SpotifySong():

    def __init__(self, id, data):

        self.id = id 
        self.raw = data 

        self.totalTime = datetime.timedelta(seconds=data)

class VoiceChannel():

    def __init__(self, id, data):

        self.id = id 
        self.raw = data 

        self.totalTime = datetime.timedelta(seconds=data["total_time"])
        self.lastSeen = LastSeen(data["last_seen"])

class Platform():

    def __init__(self, name, data):

        self.raw = data 
        self.name = name.title()

        self.totalTime = datetime.timedelta(seconds=0) if "total_time" not in data else datetime.timedelta(seconds=data["total_time"])
        self.lastSeen = LastSeen(data["last_seen"]) if "last_seen" in data else None

class User():
    class MoreStats():

        def __init__(self, statData):
            self.totalOnline = datetime.timedelta(seconds=0)
            self.lastOnline = None
            self.onlineRatio = ""

            self.loadData(statData)
        
        def loadData(self, data):

            self.totalOnline = (
                data.types.online.totalTime if data.types.online else datetime.timedelta(seconds=0)
            ) + (
                data.types.dnd.totalTime if data.types.dnd else datetime.timedelta(seconds=0)
            )

            self.onlineRatio = ratioFunction(
                self.totalOnline.total_seconds(), 
                data.types.idle.totalTime.total_seconds() if data.types.idle else 0,
                data.types.offline.totalTime.total_seconds() if data.types.offline else 0
            )

            if data.types.dnd and data.types.online:
                if data.types.dnd.lastSeen.timestamp.integer > data.types.online.lastSeen.timestamp.integer:
                    self.lastOnline = data.types.dnd.lastSeen
                else:
                    self.lastOnline = data.types.online.lastSeen
            elif data.types.dnd:
                self.lastOnline = data.types.dnd.lastSeen
            elif data.types.online:
                self.lastOnline = data.types.online.lastSeen
    
    class SpotifyStats():

        def __init__(self, user, auth : spotify.Auth):

            self.user = user
            self.client = spotify.Client(auth=auth)

            self.songList = self.client.getMultipleTrackFeatures(
                self.client.getMultipleTrackDetails(
                    tracks=self.client.getTrackListFromIDList(list(self.user.spotify))
                )
            )

            result = {}
            self.averagePopularity = 0
            self.averageLength = datetime.timedelta(seconds=0)
            self.artists = {}

            for song in self.songList:

                for artist in song.artists:
                    if artist.id not in self.artists:
                        self.artists[artist.id] = [artist, datetime.timedelta(seconds=0)]
                    
                    self.artists[artist.id][1] += self.user.spotify[song.id].totalTime

                self.averagePopularity += song.popularity
                self.averageLength += song.duration

                for feature in song.audioFeatures.supportedTypes:
                    if feature not in result:
                        result[feature] = 0
                    result[feature] += getattr(song.audioFeatures, feature)
            
            for r in result:
                result[r] = float(result[r]) / len(self.songList)
            
            self.averageFeatures = spotify.TrackAudioFeatures(result)
            self.averagePopularity /= len(self.songList)
            self.averageLength = datetime.timedelta(seconds=self.averageLength.total_seconds() / len(self.songList))

            self.artists = dict(sorted(self.artists.items(), key=lambda item: item[1][1], reverse=True))

            self.artistList = self.client.getMultipleArtists(
                self.client.getArtistListFromIDList(list(self.artists))
            )

            counter = 0 
            for artist in self.artists:
                if counter >= self.client.getMultipleArtistMax:
                    continue
                self.artists[list(self.artists)[counter]][0] = self.artistList[counter]
                counter += 1



    def __init__(self, id, data):    
        
        self.activities = {}
        self.statuses = {}
        self.spotify = {}
        self.voice = {}
        self.spotifyStats = None
        self.platforms = {}
        self.messages = 0
        
        self.id = id

        self.loadData(data)

        self.more = self.MoreStats(self)
    
    def getSpotifyStats(self, auth : spotify.Auth):
        self.spotifyStats = self.SpotifyStats(self, auth)
        return self
    
    def loadData(self, data):
        self.data = data

        activities = data["activities"]
        statuses = data["statuses"]
        types = data["types"]
        spotify = data["extensions"]["spotify"] if "spotify" in data["extensions"] else {}
        voice = data["extensions"]["voice"] if "voice" in data["extensions"] else {}
        platforms = data["extensions"]["platforms"] if "platforms" in data["extensions"] else {}

        for activityName, activityData in activities.items():
            self.activities[activityName] = Activity(activityName, activityData)
        
        for statusName, statusData in statuses.items():
            self.statuses[statusName] = Status(statusName, statusData)
        
        for songName, songData in spotify.items():
            self.spotify[songName] = SpotifySong(songName, songData)
        
        for channelId, voiceData in voice.items():
            self.voice[channelId] = VoiceChannel(channelId, voiceData)
        
        for platformName, platformData in platforms.items():
            self.platforms[platformName] = Platform(platformName, platformData)
        
        self.types = Types(types)
        self.messages = data["extensions"]["messages"] if "messages" in data["extensions"] else 0

        self.activities = dict(sorted(self.activities.items(), key=lambda item: item[1].totalTime, reverse=True))
        self.statuses = dict(sorted(self.statuses.items(), key=lambda item: item[1].totalTime, reverse=True))
        self.spotify = dict(sorted(self.spotify.items(), key=lambda item: item[1].totalTime, reverse=True))
        self.voice = dict(sorted(self.voice.items(), key=lambda item: item[1].totalTime, reverse=True))
        self.platforms = dict(sorted(self.platforms.items(), key=lambda item: item[1].totalTime, reverse=True))
    
    def get_user(self, bot):
        return bot.get_user(int(self.id))

class Stats():

    class MoreStats():

        def __init__(self, statData):
            self.totalTracked = datetime.timedelta(seconds=0)
            self.totalOnline = datetime.timedelta(seconds=0)
            self.averageOnline = datetime.timedelta(seconds=0)
            self.totalMessages = 0

            self.loadData(statData)
        
        def loadData(self, data):

            types = data.users[list(data.users)[0]].types.all

            trackedTime = datetime.timedelta(seconds=0)
            for typeName, userType in types.items():
                trackedTime += userType.totalTime
            
            self.totalTracked = trackedTime
            
            for username, user in data.users.items():
                self.totalOnline += user.more.totalOnline
                self.totalMessages += user.messages
            
            self.averageOnline = datetime.timedelta(seconds=self.totalOnline.total_seconds() / len(data.users) )
            
    def __init__(self, data = None, location = directory + "all.json"):

        self.users = {}
        self.activities = {}
        self.raw = data

        if data == None:
            self.raw = getData(location)

        self.loadData(self.raw) 

        self.more = self.MoreStats(self)

    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)
    
    def loadData(self, data):

        for user in data["users"]:
            self.users[user] = User(user, data["users"][user])
        
        self.users = dict(sorted(self.users.items(), key=lambda item: item[1].more.totalOnline, reverse=True))
        
        self.loadActivities(data)
        
    def loadActivities(self, data):
        
        for userID, user in self.users.items():

            for activityName, activity in user.activities.items():

                if activityName not in self.activities:
                    self.activities[activityName] = ListActivity(activityName)
                
                self.activities[activityName].addUser(user)
        
        self.activities = dict(sorted(self.activities.items(), key=lambda item: item[1].totalTime, reverse=True))
    
def getData(location=None):
    if location == None:
        location = directory + "all.json"

    #data = requests.get(f'http://helperdata.glitch.me/view{setup.databaseToken}/{location}')
    #return data.json()

    with open(location) as f:
        data = json.load(f)
        
        return data

def saveData(data, location=directory + "all.json"):
    #data = requests.post(f'http://helperdata.glitch.me/save{setup.databaseToken}/{location}',  data = {"data":str(json.dumps(data))})
    #return data.json()

    with open(location, "w") as f:
        return json.dump(data, f, indent=4)

def getDefaultData(blacklisted=[]):
    dtToday = datetime.datetime.today()
    day = f"{dtToday.year}/{dtToday.month}/{dtToday.day}"

    default = {
        "lastReloaded":day,
        "users":{},
        "activites": {},
        "ids": blacklisted
    }
    return default