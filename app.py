import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm, skew
import matplotlib.pyplot as plt

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("Penilaian_Kinerja.csv")

df = load_data()
jabatan_col = 'Nama_Posisi'

# Skor KPI Korporasi
skor_korporasi = df['Skor_KPI_Final'].mean()
mean_kpi = skor_korporasi
std_kpi = df['Skor_KPI_Final'].std()
skewness = skew(df['Skor_KPI_Final'])

def kategori_kpi(percentile):
    if percentile >= 0.9:
        return 'Istimewa'
    elif percentile >= 0.75:
        return 'Sangat Baik'
    elif percentile >= 0.25:
        return 'Baik'
    elif percentile >= 0.10:
        return 'Cukup'
    else:
        return 'Kurang'

# Hitung kategori & gap
hasil_komparasi = []
for idx, row in df.iterrows():
    nipp = row['NIPP_Pekerja']
    jabatan = row[jabatan_col] if jabatan_col in row else ""
    nipp_atasan = row['NIPP_Atasan']
    skor = row['Skor_KPI_Final']
    gap_vs_korporasi = (skor - skor_korporasi) / skor_korporasi
    if nipp_atasan in df['NIPP_Pekerja'].values:
        skor_atasan = df[df['NIPP_Pekerja'] == nipp_atasan]['Skor_KPI_Final'].values[0]
        gap_vs_atasan = (skor - skor_atasan) / skor_atasan
    else:
        skor_atasan = np.nan
        gap_vs_atasan = np.nan
    percentile = norm.cdf(skor, loc=mean_kpi, scale=std_kpi)
    kategori = kategori_kpi(percentile)
    hasil_komparasi.append({
        'NIPP': nipp,
        'Nama_Posisi': jabatan,
        'NIPP_Atasan': nipp_atasan,
        'Skor_KPI_Final': skor,
        'Skor_KPI_Atasan': skor_atasan,
        'Gap_vs_Atasan(%)': round(100*gap_vs_atasan, 2) if not np.isnan(gap_vs_atasan) else "",
        'Gap_vs_Korporasi(%)': round(100*gap_vs_korporasi, 2),
        'Kategori_Distribusi': kategori
    })

df_komparasi = pd.DataFrame(hasil_komparasi)

# Tabel NIPP dan Nama_Posisi per kategori distribusi
st.header("Daftar Pekerja per Kategori Distribusi Normal KPI")
for kategori in ['Istimewa', 'Sangat Baik', 'Baik', 'Cukup', 'Kurang']:
    st.subheader(f"Kategori: {kategori}")
    df_kat = df_komparasi[df_komparasi['Kategori_Distribusi'] == kategori][['NIPP', 'Nama_Posisi']]
    if df_kat.empty:
        st.write("Tidak ada.")
    else:
        st.dataframe(df_kat)

# Visualisasi kurva korporasi (umum)
st.header("Kurva Distribusi Normal KPI Seluruh Pegawai (Korporasi/Pelindo)")
fig, ax = plt.subplots(figsize=(12, 4))
x = np.linspace(90, 110, 1000)
y = norm.pdf(x, mean_kpi, std_kpi)
ax.plot(x, y, color='black', linewidth=2, label='Kurva Normal')
for label, color, low, high in [
    ('Istimewa', 'gold', 0.9, 1.0),
    ('Sangat Baik', 'green', 0.75, 0.9),
    ('Baik', 'skyblue', 0.25, 0.75),
    ('Cukup', 'orange', 0.10, 0.25),
    ('Kurang', 'red', 0.0, 0.10)
]:
    x_fill = norm.ppf([low, high], mean_kpi, std_kpi)
    mask = (x >= x_fill[0]) & (x <= x_fill[1])
    ax.fill_between(x[mask], y[mask], alpha=0.25, color=color, label=label)
ax.set_xlim(90, 110)
ax.set_xlabel('Skor KPI')
ax.set_ylabel('Densitas')
ax.set_title('Kurva Distribusi Normal Skor KPI Pegawai Pelindo')
ax.legend()
st.pyplot(fig)

# Visualisasi kurva untuk tiap atasan langsung (group head/department head) beserta bawahan
st.header("Kurva Distribusi Normal KPI untuk Tiap Atasan Langsung (Group/Dept)")
for nipp_atasan in df['NIPP_Atasan'].dropna().unique():
    if pd.isna(nipp_atasan) or nipp_atasan == '' or nipp_atasan not in df['NIPP_Pekerja'].values:
        continue
    jabatan_atasan = df[df['NIPP_Pekerja'] == nipp_atasan][jabatan_col].iloc[0]
    df_bawahan = df[df['NIPP_Atasan'] == nipp_atasan][['NIPP_Pekerja', jabatan_col, 'Skor_KPI_Final']]
    if df_bawahan.empty:
        continue
    mean_local = df_bawahan['Skor_KPI_Final'].mean()
    std_local = df_bawahan['Skor_KPI_Final'].std()
    fig, ax = plt.subplots(figsize=(12, 3))
    x = np.linspace(90, 110, 1000)
    y = norm.pdf(x, mean_local, std_local)
    ax.plot(x, y, color='black', linewidth=2, label='Kurva Normal (bawahan)')
    ax.set_xlim(90, 110)
    ax.set_xlabel('Skor KPI')
    ax.set_ylabel('Densitas')
    ax.set_title(f"Bawahan dari Atasan: {jabatan_atasan}")
    st.pyplot(fig)

# Statistik ringkas
st.header("Statistik Distribusi Seluruh Pegawai")
st.markdown(f"- **Rata-rata (Korporasi/Pelindo):** {mean_kpi:.2f}")
st.markdown(f"- **Standard Deviasi:** {std_kpi:.2f}")
st.markdown(f"- **Skewness:** {skewness:.2f}")

# Sebaran kategori (tabel persentase)
st.markdown("### Sebaran Persentase Kategori Distribusi Normal")
distribusi = df_komparasi['Kategori_Distribusi'].value_counts(normalize=True).reindex(
    ['Istimewa', 'Sangat Baik', 'Baik', 'Cukup', 'Kurang']
).fillna(0) * 100
st.table(distribusi.reset_index().rename(columns={'index':'Kategori','Kategori_Distribusi':'Persentase (%)'}))
