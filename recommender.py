import pickle
import pandas as pd
import numpy as np

# Load DataFrame and energy similarity mapping from pickle files
df = pickle.load(open('df.pkl', 'rb'))
songs_count = df.shape[0]
energy_similarity_mapping = pickle.load(open('energy_similarity_mapping.pkl', 'rb'))

def sort_by_popularity(songs, descending=True):
    if descending:
        return songs.sort_values(by=['Popularity'], ascending=False)
    else:
        return songs.sort_values(by=['Popularity'])

def get_similar(track_index, count, comparison_matrix, select_smallest):
    similar_songs_indexes = np.argsort(np.array(comparison_matrix[track_index]))
    similar_songs_indexes = np.delete(similar_songs_indexes, np.where(similar_songs_indexes == track_index))
    similar_songs_indexes = similar_songs_indexes[:count] if select_smallest else similar_songs_indexes[::-1][:count]
    return df.iloc[similar_songs_indexes].copy()

def recommendations_as_list(songs, include_fields):
    songs = songs[include_fields].copy()
    songs['index'] = songs.index
    return songs.to_dict(orient='records')

def get_closest_n(track_index, count):
    # Ambil tanggal dari track_index
    target_date = pd.to_datetime(track_index)
    
    # Hitung perbedaan absolut antara setiap tanggal dalam DataFrame dan target_date
    df['Date Difference'] = (df['Album Release Date'] - target_date).abs()
    
    # Urutkan DataFrame berdasarkan perbedaan tanggal
    df_sorted = df.sort_values(by='Date Difference')
    
    # Ambil indeks lagu terdekat (kecuali indeks lagu track_index itu sendiri)
    closest_indexes = df_sorted.index[df_sorted.index != track_index][:count]
    
    # Ambil baris DataFrame yang sesuai dengan indeks lagu terdekat
    closest_songs = df.loc[closest_indexes]
    
    return closest_songs


def get_metadata(track_index):
    return df.iloc[track_index][['Track Name', 'Artist Name(s)']].to_dict()

def get_by_same_artist(track_index, count):
    return df[df['Artist Name(s)'] == df.iloc[track_index]['Artist Name(s)']].drop(track_index)[:count]

def get_energy_similar(track_index, count):
    similar_songs_indexes = energy_similarity_mapping[track_index][:count]
    return df.iloc[similar_songs_indexes].copy()

def get_random(count):
    return df.sample(count)

def get_released_around_same_time(track_index, count):
    return get_closest_n(track_index, count)

def recommend_by_same_artist(track_index, count, prioritisePopular, include_fields):
    songs_by_same_artist = get_by_same_artist(track_index, count*2)
    songs_by_same_artist = sort_by_popularity(songs_by_same_artist, prioritisePopular)[:count]
    return recommendations_as_list(songs_by_same_artist, include_fields)

def recommend_energy_similar(track_index, count, prioritisePopular, include_fields):
    similar_songs = get_energy_similar(track_index, count*2)
    similar_songs = sort_by_popularity(similar_songs, prioritisePopular)[:count]
    return recommendations_as_list(similar_songs, include_fields)

def recommend_released_around_same_time(track_index, count, prioritisePopular, include_fields):
    contemporary_songs = None
    years_range = [1, 2, 3]  # Coba hingga tiga rentang waktu yang berbeda
    for years in years_range:
        contemporary_songs = get_released_around_same_time(track_index, count*2)
        if contemporary_songs is not None:
            break  # Jika lagu-lagu ditemukan, keluar dari loop
    if contemporary_songs is not None:
        contemporary_songs = sort_by_popularity(contemporary_songs, prioritisePopular)[:count]
        return recommendations_as_list(contemporary_songs, include_fields)
    else:
        # Jika tidak ada lagu yang ditemukan dalam semua rentang waktu yang dicoba, kembalikan daftar kosong
        return []


def recommend_random(count, prioritisePopular, include_fields):
    random_songs = get_random(count*2)
    random_songs = sort_by_popularity(random_songs, prioritisePopular)[:count]
    return recommendations_as_list(random_songs, include_fields)

def hybrid_recommend(track_index, count=5, prioritisePopular=True):
    include_fields = ['track_name', 'track_artist']
    all_recommendations = dict()
    all_recommendations['by same artist'] = recommend_by_same_artist(track_index, count, prioritisePopular, include_fields)
    all_recommendations['similar energy'] = recommend_energy_similar(track_index, count, prioritisePopular, include_fields)
    all_recommendations['released around same time'] = recommend_released_around_same_time(track_index, count, prioritisePopular, include_fields)
    all_recommendations['random'] = recommend_random(count, prioritisePopular, include_fields)
    return all_recommendations
