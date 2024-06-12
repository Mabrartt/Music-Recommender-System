import pickle
import streamlit as st
import pandas as pd
import spotipy
import base64
from spotipy.oauth2 import SpotifyClientCredentials
from recommender import recommend_released_around_same_time, recommend_energy_similar, recommend_by_same_artist, sort_by_popularity

# Set page configuration
st.set_page_config(
    page_title="Music Recommender System",
    page_icon="🎶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fungsi untuk mengatur gambar latar belakang
def set_background_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_string}");
            background-size: cover;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Ganti 'background.png' dengan nama file gambar yang telah Anda unggah
set_background_image('background2.png')

# Inisialisasi Spotify Client
client_id = "ae17caf9fa0c4a609add4de382286a73"
client_secret = "c8a47e39a62845c2a94553bfb1dcbbe0"
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def get_song_album_cover_url(song_name):
    result = sp.search(q='track:' + song_name, type='track')
    if result['tracks']['items']:
        cover_url = result['tracks']['items'][0]['album']['images'][0]['url']
        return cover_url
    else:
        return "https://i.postimg.cc/0QNxYz4V/social.png"

def get_song_preview_url(song_name):
    result = sp.search(q='track:' + song_name, type='track')
    if result['tracks']['items']:
        preview_url = result['tracks']['items'][0]['preview_url']
        return preview_url
    else:
        return None

def get_song_album_cover_urls(songs):
    cover_urls = []
    for song in songs:
        cover_urls.append(get_song_album_cover_url(song))
    return cover_urls

def recommend_by_same_artist(artist_name, count, prioritisePopular, include_fields):
    df = pickle.load(open('df.pkl', 'rb'))
    energy_similarity_mapping = pickle.load(open('energy_similarity_mapping.pkl', 'rb'))

    artist_name_lower = artist_name.lower()
    df['Artist Name(s)_lower'] = df['Artist Name(s)'].str.lower()
    artist_songs = df[df['Artist Name(s)_lower'] == artist_name_lower]

    if artist_songs.empty:
        return {field: [] for field in include_fields}

    recommendations = get_by_same_artist(artist_songs.index[0], count, prioritisePopular, include_fields, df, energy_similarity_mapping)
    return recommendations

def get_by_same_artist(track_index, count, prioritisePopular, include_fields, df, energy_similarity_mapping):
    track_index = int(track_index)
    similar_songs_indexes = energy_similarity_mapping[track_index][:count]
    similar_songs = df.iloc[similar_songs_indexes]
    similar_songs = sort_by_popularity(similar_songs, prioritisePopular)
    recommendations = recommendations_as_list(similar_songs, include_fields)
    return recommendations

def sort_by_popularity(songs, descending=True):
    if descending:
        return songs.sort_values(by=['Popularity'], ascending=False)
    else:
        return songs.sort_values(by=['Popularity'])

def recommendations_as_list(songs, include_fields):
    songs = songs[include_fields].copy()
    songs['index'] = songs.index
    return songs.to_dict(orient='records')

def recommend(song, only_with_preview):
    similarity = pickle.load(open('simis.pkl', 'rb'))
    music = pd.read_csv('dataset.csv')
    index = music[music['Track Name'] == song].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_music_names = []
    recommended_music_posters = []
    recommended_music_previews = []
    for i in distances[1:6]:
        track_name = music.iloc[i[0]]['Track Name']
        preview_url = get_song_preview_url(track_name)
        if only_with_preview and not preview_url:
            continue
        recommended_music_posters.append(get_song_album_cover_url(track_name))
        recommended_music_names.append(track_name)
        recommended_music_previews.append(preview_url)

    return recommended_music_names, recommended_music_posters, recommended_music_previews

# Streamlit App
st.title('🎶 Music Recommender System 🎶')

music = pd.read_csv('dataset.csv')
music_list = music['Track Name'].tolist()

st.subheader("Select a Song")
selected_song = st.selectbox(
    "Type or select a song from the dropdown",
    music_list
)

only_with_preview = st.checkbox('Show only songs with preview')

if st.button('Show Recommendation'):
    recommended_music_names, recommended_music_posters, recommended_music_previews = recommend(selected_song, only_with_preview)
    st.subheader("Recommended Songs")
    cols = st.columns(5)
    for col, name, poster, preview in zip(cols, recommended_music_names, recommended_music_posters, recommended_music_previews):
        col.text(name)
        col.image(poster)
        if preview:
            col.audio(preview)
        else:
            col.text("No preview available")

st.sidebar.title("Recommendation Settings")
recommendation_type = st.sidebar.selectbox(
    "Select recommendation type",
    ["By Artist", "By Release Date", "By Energy"]
)

def display_recommendations(recommendations):
    cols = st.columns(5)
    for i, col in enumerate(cols):
        if i < len(recommendations):
            col.text(recommendations[i]['Track Name'])
            col.image(get_song_album_cover_url(recommendations[i]['Track Name']))
            preview_url = get_song_preview_url(recommendations[i]['Track Name'])
            if preview_url:
                col.audio(preview_url)
            else:
                col.text('No Preview')

if recommendation_type == "By Artist":
    artist_name = st.sidebar.text_input("Enter artist name")
    prioritisePopular = st.sidebar.checkbox("Prioritize popular songs")
    include_fields = ['Track Name', 'Artist Name(s)']
    count = 5
    if st.sidebar.button('Show Artist Recommendations'):
        recommendations = recommend_by_same_artist(artist_name, count, prioritisePopular, include_fields)
        display_recommendations(recommendations)

if recommendation_type == "By Release Date":
    release_date = st.sidebar.date_input("Enter release date")
    prioritisePopular = st.sidebar.checkbox("Prioritize popular songs")
    include_fields = ['Track Name', 'Artist Name(s)']
    count = 5
    if st.sidebar.button('Show Release Date Recommendations'):
        recommendations = recommend_released_around_same_time(release_date, count, prioritisePopular, include_fields)
        display_recommendations(recommendations)

if recommendation_type == "By Energy":
    energy_level = st.sidebar.slider("Select energy level", 0, 100, 50)
    prioritisePopular = st.sidebar.checkbox("Prioritize popular songs")
    include_fields = ['Track Name', 'Artist Name(s)']
    count = 5
    if st.sidebar.button('Show Energy Recommendations'):
        recommendations = recommend_energy_similar(energy_level, count, prioritisePopular, include_fields)
        display_recommendations(recommendations)

# Footer
st.markdown(
    """
    <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #f1f1f1;
            color: black;
            text-align: center;
            padding: 10px;
        }
    </style>
    <div class="footer">
        <p>Made with ❤️ by Your Name</p>
    </div>
    """,
    unsafe_allow_html=True
)