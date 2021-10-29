import requests, datetime

base = 'https://api.spotify.com/v1/'
auth = 'https://accounts.spotify.com/api/token'

class Auth():

    def __init__(self, id, secret):

        self.id = id 
        self.secret = secret
    
    def login(self):

        auth_response = requests.post(auth, {
            'grant_type': 'client_credentials',
            'client_id': self.id,
            'client_secret': self.secret,
        })

        auth_response_data = auth_response.json()
        self.token = auth_response_data['access_token']

class TrackAudioFeatures():

    def __init__(self, features):
        self.supportedTypes = ["danceability", "energy", "speechiness", "acousticness", "instrumentalness", "liveness", "valence", "tempo"]

        for feature in features:
            if feature in self.supportedTypes:
                setattr(self, feature, features[feature])
        
        self.supportedTypes = sorted(self.supportedTypes, key=lambda item: getattr(self, item), reverse=True)

class Track():

    def __init__(self, id : str = None):

        self.id = id

    def setDetails(self, data):

        self.name = data["name"]
        self.uri = data["uri"]
        self.url = data["external_urls"]["spotify"]
        self.previewURL = data["preview_url"]
        self.trackNumber = data["track_number"]
        self.explicit = data["explicit"]
        self.duration = datetime.timedelta(milliseconds=data["duration_ms"])
        self.popularity = data["popularity"]
        self.markets = data["available_markets"]
        self.id = data["id"]
        self.artists = []

        for artistData in data["artists"]:
            a = Artist()
            a.setDetails(artistData)

            self.artists.append(a)

        self.album = Album()
        self.album.setDetails(data["album"])
    
    def setAudioFeatures(self, data):

        result = {}
        supportedTypes = ["danceability", "energy", "loudness", "speechiness", "acousticness", "instrumentalness", "liveness", "valence", "tempo"]

        for feature in data:
            if feature in supportedTypes:
                result[feature] = data[feature]
        
        self.audioFeatures = TrackAudioFeatures(result)

        return self

class Album():

    def __init__(self, id : str = None):

        self.id = id 
    
    def setDetails(self, data):

        self.type = data["album_type"]
        self.markets = data["available_markets"]
        self.name = data["name"]
        self.uri = data["uri"]
        self.totalTracks = data["total_tracks"]
        self.releaseDate = datetime.datetime.strptime(data["release_date"], '%Y-%m-%d')
        self.artists = []

        for artistData in data["artists"]:
            a = Artist()
            a.setDetails(artistData)

            self.artists.append(a)

class Artist():

    def __init__(self, id : str = None):

        self.id = id 
    
    def setDetails(self, data):

        self.url = data["external_urls"]["spotify"]
        self.id = data["id"]
        self.name = data["name"]
        self.type = data["type"]
        self.uri = data["uri"]
    
    def setFullDetails(self, data):

        self.setDetails(data)

        self.genres = data["genres"]
        self.followers = data["followers"]["total"]

class Client():

    def __init__(self, auth : Auth):

        self.auth = auth

        self.auth.login()

        self.headers = {
            'Authorization': f'Bearer {self.auth.token}'
        }
    
    def makeGetRequest(self, path : str):

        return requests.get(base + path, headers=self.headers)
    
    def getTrackListFromIDList(self, tracks : list):

        result = [] 

        for track in tracks:
            result.append(Track(track))
        
        return result
    
    def getArtistListFromIDList(self, artists : list):

        result = [] 

        for artist in artists:
            result.append(Artist(artist))
        
        return result
    
    def getTrackDetails(self, track : Track):

        r = self.makeGetRequest(f"tracks/{track.id}")
        data = r.json()

        track.setDetails(data)

        return track
    
    getTrackDetailMax = 50
    getTrackFeatureMax = 100
    getMultipleArtistMax = 50
    
    def getMultipleTrackDetails(self, tracks : list):

        tracks = tracks[:self.getTrackDetailMax]

        r = self.makeGetRequest(f"tracks?ids={','.join([track.id for track in tracks])}")
        data = r.json()

        results = []

        for trackData in data["tracks"]:
            t = Track()
            t.setDetails(trackData)

            results.append(t)

        return results
    
    def getMultipleTrackFeatures(self, tracks : list):

        tracks = tracks[:self.getTrackFeatureMax]

        r = self.makeGetRequest(f"audio-features?ids={','.join([track.id for track in tracks])}")
        data = r.json()

        trackList = tracks
        counter = 0

        for audioFeatures in data["audio_features"]:
            
            trackList[counter].setAudioFeatures(audioFeatures)


            counter += 1

        return trackList
    
    def getMultipleArtists(self, artists : list):

        artists = artists[:self.getMultipleArtistMax]

        r = self.makeGetRequest(f"artists?ids={','.join([artist.id for artist in artists])}")
        data = r.json()

        artistList = artists
        counter = 0

        for artistData in data["artists"]:
            
            artistList[counter].setFullDetails(artistData)

            counter += 1

        return artistList
