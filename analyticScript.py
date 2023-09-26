import json
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 \
    import Features, KeywordsOptions

from dotenv import load_dotenv

import os
import pandas as pd
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from lyricsgenius import Genius
import requests
from requests.exceptions import HTTPError, Timeout
import tkinter as tk

load_dotenv()
Genius_Key = os.getenv("Genius_Key")
IBM_AUTH = os.getenv("IBM_AUTH")
Spotify_Client_ID = os.getenv("client_id")
Spotify_Client_Secret = os.getenv("client_secret")



def lyrics(v1, v2): 
    print("Starting Lyric Extraction")
    
    genius = Genius(Genius_Key)

    song = v1
    artist = v2

    song_search = genius.search_song(song, artist)


    with open("lyrics.json", "w") as f:
        json.dump(song_search.lyrics, f, indent=4)
    
    print("Done with Lyrics")
    key_phrase_extractor(song)

def key_phrase_extractor(song):
    print("Starting Phrase analysis")

    authenticator = IAMAuthenticator(IBM_AUTH)
    
    natural_language_understanding = NaturalLanguageUnderstandingV1(
        version='2022-04-07',
        authenticator=authenticator
    )

    with open('lyrics.json', 'r') as f:
        data = json.load(f)

    natural_language_understanding.set_service_url('https://api.us-east.natural-language-understanding.watson.cloud.ibm.com/instances/b10d8f28-59ae-43e6-a300-5b3a6177245d')

    response = natural_language_understanding.analyze(
        text=data,
        features=Features(keywords=KeywordsOptions(sentiment=True,emotion=True,limit=20))).get_result()

    with open("currentData.json", "w") as f:
            json.dump(response, f, indent = 4)

    print("ending Analysis")

    analytics(song)


def analytics(song):
    print("starting Valence analytic")
    with open('currentData.json', 'r') as f:
        data = json.load(f)["keywords"]


    df = pd.DataFrame(data)

    sentiment_dF = pd.DataFrame(df['sentiment'])

# print(mainDF)
    count = 0
    total = 0

    for index, row in sentiment_dF.iterrows():
        count += sentiment_dF['sentiment'].iloc[index]['score']
        total = total + 1


    total = total * 2
    final_val = count/total

    valence = .5+final_val

    print(valence)
    
    spotify_read(valence, song)


def spotify_read(valence_val, song):
    scope_vals = ["user-library-read", "playlist-modify-private", "playlist-modify-public"]

    sp_oauth = SpotifyOAuth(client_id=Spotify_Client_ID, client_secret=Spotify_Client_Secret, redirect_uri='http://localhost:8080/', scope=scope_vals)  


    sp = spotipy.Spotify(auth_manager=sp_oauth)

    results = sp.search(q=song, type='track')
    track_uri = results['tracks']['items'][0]['uri']

    recommendations = sp.recommendations(seed_tracks=[track_uri], target_valence=valence_val)['tracks']
    # Create a playlist  
    user_id = sp.current_user()["id"]

    new_playlist = sp.user_playlist_create(user_id, song+ " Lyrics Based Playlist", public=True, collaborative=False, description= "This playlist was curated by the lyrics of the song "+ song)
    


    track_list = []
    for track in recommendations:
        song_search = sp.search(q=track['name'], type='track')

        track_uri = song_search['tracks']['items'][0]['uri']

        track_list.append(track_uri)


    sp.user_playlist_add_tracks(user_id, new_playlist['id'], track_list, position=None)
    print("done.")

        
    










def main():
    # lyrics(SONG_CHOICE, ARTIST)
    # print("Playlist Created.")
    root= tk.Tk()
    label1 = tk.Label(root, text="Enter Song Here:")
    canvas1 = tk.Canvas(root, width=400, height=300)
    label1.pack()
    canvas1.pack()

    label2 = tk.Label(root, text="Enter Artist Here:")
    canvas2 = tk.Canvas(root, width = 400, height = 300)
    label2.pack()
    canvas2.pack()



    entry1 = tk.Entry(root)
    entry2 = tk.Entry(root)
    canvas1.create_window(200, 140, window=entry1)
    canvas2.create_window(200,140, window=entry2)


    def run_now():  
        SONG_CHOICE = entry1.get()
        ARTIST_CHOICE = entry2.get()
        



        lyrics(SONG_CHOICE, ARTIST_CHOICE)
        label1 = tk.Label(text = "Done")
        canvas1.create_window(200,230, window = label1)

        
    button1 = tk.Button(text='Start Now', command=run_now)
    canvas2.create_window(200, 180, window=button1)

    root.mainloop()
    

main()


