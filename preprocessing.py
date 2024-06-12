import pickle
import pandas as pd
import numpy as np
from sklearn.metrics import euclidean_distances

# Baca dataset
df = pd.read_csv('E:\\streamlit_music\\dataset.csv')

# Buang kolom yang tidak diperlukan
df.drop(columns=['Track Preview URL', 'Time Signature', 'Copyrights'], inplace=True)

# Hapus duplikat berdasarkan judul lagu dan nama artis
df.drop_duplicates(subset=['Track Name', 'Artist Name(s)'], inplace=True)

# Ubah format tanggal rilis album menjadi datetime
df['Album Release Date'] = pd.to_datetime(df['Album Release Date'], infer_datetime_format=True, errors='coerce')

# Urutkan berdasarkan tanggal rilis album
df.sort_values(by=['Album Release Date'], inplace=True)
df.reset_index(drop=True, inplace=True)

# Hitung jumlah lagu
songs_count = df.shape[0]

# Kolom yang diperlukan untuk kategori energi dan suasana hati
required_columns_energy = ['Danceability', 'Tempo', 'Acousticness']
required_columns_mood = ['Mode', 'Key', 'Valence']

# Buang baris dengan nilai null pada kolom energi
df_cleaned = df.dropna(subset=required_columns_energy)

# Pisahkan data energi dan suasana hati
energy_data = df_cleaned[required_columns_energy]

# Hitung matriks jarak Euclidean untuk data energi
energy_difference_matrix = euclidean_distances(energy_data)

# Fungsi untuk mendapatkan indeks lagu yang mirip
def get_similar_indices(track_index, count, comparison_matrix, select_smallest):
    similar_songs_indexes = np.argsort(np.array(comparison_matrix[track_index]))
    similar_songs_indexes = np.delete(similar_songs_indexes, np.where(similar_songs_indexes == track_index))
    return similar_songs_indexes[:count] if select_smallest else similar_songs_indexes[::-1][:count]

# Inisialisasi pemetaan kemiripan energi
energy_similarity_mapping = dict()

# Isi pemetaan kemiripan energi
for i in range(songs_count):
    energy_similarity_mapping[i] = get_similar_indices(i, 20, energy_difference_matrix, True)

# Simpan DataFrame dan pemetaan kemiripan energi ke dalam file pickle
with open('df.pkl', 'wb') as f:
    pickle.dump(df, f)

with open('energy_similarity_mapping.pkl', 'wb') as f:
    pickle.dump(energy_similarity_mapping, f)
