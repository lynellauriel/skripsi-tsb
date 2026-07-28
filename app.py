import streamlit as st

# Deklarasi Halaman Kustom
dashboard_page = st.Page("pages/1_Dashboard.py", title="Dashboard Utama", icon="📊")
barang_page = st.Page("pages/2_Data_Barang.py", title="Kelola Data Barang", icon="📦")
transaksi_page = st.Page("pages/3_Data_Transaksi.py", title="Riwayat & Transaksi", icon="🛒")
tsb_page = st.Page("pages/4_Peramalan_TSB.py", title="Peramalan Metode TSB", icon="⭐")
peramalan_page = st.Page("pages/5_Hasil_Peramalan.py", title="Hasil Peramalan", icon="📄")
laporan_page = st.Page("pages/6_Laporan.py", title="Laporan System", icon="📈")

# Kelompokkan dan Jalankan Navigasi
pg = st.navigation({
    "Menu Utama": [dashboard_page],
    "Manajemen Gudang": [barang_page, transaksi_page],
    "Purchasing & Forecasting": [tsb_page, peramalan_page, laporan_page]
})

pg.run()