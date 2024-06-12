import pickle
import streamlit as st
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from recommender import recommend_released_around_same_time, recommend_energy_similar, recommend_by_same_artist, sort_by_popularity

# Inisialisasi Spotify Client
client_id = "ae17caf9fa0c4a609add4de382286a73"
client_secret = "c8a47e39a62845c2a94553bfb1dcbbe0"
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def get_song_album_cover_url(song_name):
    # Cari lagu menggunakan Spotify API
    result = sp.search(q='track:' + song_name, type='track')
    if result['tracks']['items']:
        # Ambil URL sampul album dari hasil pencarian
        cover_url = result['tracks']['items'][0]['album']['images'][0]['url']
        return cover_url
    else:
        return "https://i.postimg.cc/0QNxYz4V/social.png"

def recommend_by_same_artist(artist_name, count, prioritisePopular, include_fields):
    df = pickle.load(open('df.pkl', 'rb'))
    energy_similarity_mapping = pickle.load(open('energy_similarity_mapping.pkl', 'rb'))
    # Find songs by the artist
    artist_songs = df[df['Artist Name(s)'] == artist_name]

    # If no songs found by the artist, return empty recommendations
    if artist_songs.empty:
        return {field: [] for field in include_fields}

    # Get recommendations based on the artist using your model function
    recommendations = get_by_same_artist(artist_songs.index[0], count, prioritisePopular, include_fields, df, energy_similarity_mapping)
    return recommendations

def get_by_same_artist(track_index, count, prioritisePopular, include_fields, df, energy_similarity_mapping):
    track_index = int(track_index)  # Convert to integer type
    similar_songs_indexes = energy_similarity_mapping[track_index][:count]
    similar_songs = df.iloc[similar_songs_indexes]
    similar_songs = sort_by_popularity(similar_songs, prioritisePopular)
    return recommendations_as_list(similar_songs, include_fields)


def sort_by_popularity(songs, descending=True):
    if descending:
        return songs.sort_values(by=['Popularity'], ascending=False)
    else:
        return songs.sort_values(by=['Popularity'])

def recommendations_as_list(songs, include_fields):
    songs = songs[include_fields].copy()
    songs['index'] = songs.index
    return songs.to_dict(orient='records')

def recommend(song):
    # Load similarity matrix
    similarity = pickle.load(open('simis.pkl', 'rb'))
    # Load dataset
    music = pd.read_csv('dataset.csv')
    index = music[music['Track Name'] == song].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_music_names = []
    recommended_music_posters = []
    for i in distances[1:6]:
        recommended_music_posters.append(get_song_album_cover_url(music.iloc[i[0]]['Track Name']))
        recommended_music_names.append(music.iloc[i[0]]['Track Name'])

    return recommended_music_names, recommended_music_posters

st.header('Music Recommender System')

# Load dataset
music = pd.read_csv('dataset.csv')
music_list = music['Track Name'].tolist()  # Mengambil daftar lagu dari kolom 'Track Name'

selected_song = st.selectbox(
    "Type or select a song from the dropdown",
    music_list
)

if st.button('Show Recommendation'):
    recommended_music_names, recommended_music_posters = recommend(selected_song)
    col1, col2, col3, col4, col5= st.columns(5)
    with col1:
        st.text(recommended_music_names[0])
        st.image(recommended_music_posters[0])
    with col2:
        st.text(recommended_music_names[1])
        st.image(recommended_music_posters[1])
    with col3:
        st.text(recommended_music_names[2])
        st.image(recommended_music_posters[2])
    with col4:
        st.text(recommended_music_names[3])
        st.image(recommended_music_posters[3])
    with col5:
        st.text(recommended_music_names[4])
        st.image(recommended_music_posters[4])

recommendation_type = st.sidebar.selectbox(
    "Select recommendation type",
    ["By Artist", "By Release Date", "By Energy"]
)

if recommendation_type == "By Artist":
    artist_name = st.text_input("Enter artist name")
    prioritisePopular = st.checkbox("Prioritize popular songs")
    include_fields = ['Track Name', 'Artist Name(s)']
    count = 5
    recommendations = recommend_by_same_artist(artist_name, count, prioritisePopular, include_fields)
    st.write(recommendations)
    # Add UI elements and logic to get artist name and display recommendations
    # pass  # Replace 'pass' with the actual implementation

if recommendation_type == "By Release Date":
    release_date = st.date_input("Enter release date")
    prioritisePopular = st.checkbox("Prioritize popular songs")
    include_fields = ['Track Name', 'Artist Name(s)']
    count = 5
    recommendations = recommend_released_around_same_time(release_date, count, prioritisePopular, include_fields)
    st.write(recommendations)
    # Add UI elements and logic to get release date and display recommendations
    # pass  # Replace 'pass' with the actual implementation

if recommendation_type == "By Energy":
    energy_level = st.sidebar.slider("Select energy level", 0, 100, 50)
    prioritisePopular = st.sidebar.checkbox("Prioritize popular songs")
    include_fields = ['Track Name', 'Artist Name(s)']
    count = 5
    recommendations = recommend_energy_similar(energy_level, count, prioritisePopular, include_fields)
    st.write(recommendations)