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

# Pastikan kolom jabatan ada dan konsisten
jabatan_col = 'Jabatan' if 'Jabatan' in df.columns else 'Posisi'

# 1. Skor KPI Korporasi (rata-rata seluruh pekerja)
skor_korporasi = df['Skor_KPI_Final'].mean()

# 2. Statistik distribusi untuk kategorisasi kurva normal
mean_kpi = skor_korporasi
std_kpi = df['Skor_KPI_Final'].std()
skewness = skew(df['Skor_KPI_Final'])

# 3. Siapkan kategori distribusi sesuai persentil (default mapping)
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

# 4. Siapkan tabel perbandingan atasan-bawahan
hasil_komparasi = []
for idx, row in df.iterrows():
    nipp = row['NIPP_Pekerja']
    nama = row['Nama_Pekerja'] if 'Nama_Pekerja' in df.columns else ""
    jabatan = row[jabatan_col] if jabatan_col in row else ""
    nipp_atasan = row['NIPP_Atasan']
    skor = row['Skor_KPI_Final']

    # Gap dengan skor korporasi
    gap_vs_korporasi = (skor - skor_korporasi) / skor_korporasi

    # Gap dengan atasan (jika ada)
    if nipp_atasan in df['NIPP_Pekerja'].values:
        skor_atasan = df[df['NIPP_Pekerja'] == nipp_atasan]['Skor_KPI_Final'].values[0]
        gap_vs_atasan = (skor - skor_atasan) / skor_atasan
    else:
        skor_atasan = np.nan
        gap_vs_atasan = np.nan

    # Posisi skor di distribusi normal (percentile)
    percentile = norm.cdf(skor, loc=mean_kpi, scale=std_kpi)
    kategori = kategori_kpi(percentile)

    hasil_komparasi.append({
        'NIPP': nipp,
        'Nama': nama,
        'Jabatan': jabatan,
        'NIPP_Atasan': nipp_atasan,
        'Skor_KPI_Final': skor,
        'Skor_KPI_Atasan': skor_atasan,
        'Gap_vs_Atasan(%)': round(100*gap_vs_atasan, 2) if not np.isnan(gap_vs_atasan) else "",
        'Gap_vs_Korporasi(%)': round(100*gap_vs_korporasi, 2),
        'Kategori_Distribusi': kategori
    })

df_komparasi = pd.DataFrame(hasil_komparasi)

# 5. Statistik distribusi
distribusi = df_komparasi['Kategori_Distribusi'].value_counts(normalize=True).reindex(
    ['Istimewa', 'Sangat Baik', 'Baik', 'Cukup', 'Kurang']
).fillna(0) * 100

# 6. Visualisasi kurva distribusi normal
fig, ax = plt.subplots(figsize=(12, 5))
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
ax.set_xlabel('Skor KPI')
ax.set_ylabel('Densitas')
ax.set_title('Kurva Distribusi Normal Skor KPI Pegawai Pelindo')
ax.legend()

# === Streamlit output ===
st.subheader("Statistik Distribusi Skor KPI Pegawai Pelindo")
st.markdown(f"- **Rata-rata (Korporasi/Pelindo):** {mean_kpi:.2f}")
st.markdown(f"- **Standard Deviasi:** {std_kpi:.2f}")
st.markdown(f"- **Skewness:** {skewness:.2f}")
st.markdown("### Tabel Hasil Perbandingan Atasan vs Bawahan vs Korporasi")
st.dataframe(df_komparasi)
st.markdown("### Sebaran Kategori Distribusi Normal (Persentase)")
st.table(distribusi.reset_index().rename(columns={'index':'Kategori','Kategori_Distribusi':'Persentase (%)'}))
st.pyplot(fig)
