import json

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
import os
import youtube_dl
from youtube_dl.utils import ExtractorError

from secrets import spotify_user_id, spotify_token


class CreatePlaylist:

    def __init__(self):
        self.user_id = spotify_user_id
        self.spotify_token = spotify_token
        self.youtube_client = self.get_youtube_client()
        self.all_song_info = {}

    def get_youtube_client(self):
        """ Log Into Youtube, Copied from Youtube Data API """
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

    def get_liked_videos(self):
        request = self.youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like"
        )

        response = request.execute()

        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(
                item["id"])

            try:
                video = youtube_dl.YoutubeDL({}).extract_info(
                youtube_url, download=False)
                song_name = video["track"]
                artist = video["artist"]
            except:
                song_name = "Roses (Imanbek Remix)"
                artist = "SAINt JHN"


            self.all_song_info[video_title] = {
                "youtube_url": youtube_url,
                "song_name": song_name,
                "artist": artist,

                "spotify_uri": self.get_spotify_uri(song_name, artist)}

    def create_spotify_playlist(self):

        request_body = json.dumps({
            "name": "testpl",
            "description": "my python",
            "public": True
        })
        query = "https://api.spotify.com/v1/users/{}/playlists".format(
            self.user_id)

        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
        response_json = response.json()

        return response_json["id"]

    def get_spotify_uri(self, song_name, artist):
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(
            song_name,
            artist
        )
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
        response_json = response.json()
        print(response_json)
        songs = response_json["tracks"]["items"]

        uri = songs[0]["uri"]
        print(uri)

        return uri

    def add_song_to_playlist(self):
        self.get_liked_videos()
        print('we here')

        uris = [info["spotify_uri"]
                for song, info in self.all_song_info.items()]

        playlist_id = self.create_spotify_playlist()

        request_data = json.dumps(uris)

        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(
            playlist_id)

        response = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )



        response_json = response.json()
        return response_json
if __name__ == '__main__':
    cp = CreatePlaylist()
    cp.add_song_to_playlist()
