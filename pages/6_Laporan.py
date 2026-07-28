import streamlit as st
import pandas as pd
import io
from datetime import datetime
from utils import check_login, init_session_state

init_session_state()
check_login()

st.header("📄 Modul Laporan & Export Data")

def convert_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

t1, t2, t3, t4 = st.tabs(["Laporan Daftar Barang", "Laporan Transaksi", "Laporan Peramalan", "Laporan Khusus"])

with t1:
    df_b = st.session_state['df_barang']
    if df_b.empty:
        st.write("Data masih kosong.")
    else:
        st.dataframe(df_b)
        st.download_button("📥 Unduh Excel (Daftar Barang)", data=convert_to_excel(df_b), file_name='Laporan_Daftar_Barang.xlsx')

with t2:
    df_t = st.session_state['df_transaksi']
    if df_t.empty:
        st.write("Data masih kosong.")
    else:
        st.dataframe(df_t)
        st.download_button("📥 Unduh Excel (Transaksi)", data=convert_to_excel(df_t), file_name='Laporan_Transaksi.xlsx')

with t3:
    df_p = st.session_state['df_peramalan']
    if df_p.empty:
        st.write("Data masih kosong.")
    else:
        st.dataframe(df_p)
        st.download_button("📥 Unduh Excel (Peramalan TSB)", data=convert_to_excel(df_p), file_name='Laporan_Hasil_Peramalan_TSB.xlsx')


with t4:
    st.caption("Pilih jenis laporan khusus yang ingin Anda preview dan unduh ke format CSV.")

    # Data Source dari Session State
    df_t = st.session_state.get('df_transaksi', pd.DataFrame()).copy()
    df_b = st.session_state.get('df_barang', pd.DataFrame()).copy()
    df_ramalan = st.session_state.get('df_hasil_ramalan_terakhir', pd.DataFrame()).copy()

    # ==========================================
    # 1. PILIHAN JENIS LAPORAN
    # ==========================================
    col_opt, col_blank = st.columns([2, 1])

    with col_opt:
        jenis_laporan = st.selectbox(
            "📌 Pilih Jenis Laporan Khusus:",
            [
                "Laporan Transaksi Keluar Only",
                "Laporan Transaksi Masuk Only",
                "Laporan Hasil Peramalan TSB (Terakhir)"
            ]
        )

    st.markdown("---")

    # Variables penampung
    df_export = pd.DataFrame()
    filename_out = "laporan.csv"

    # ==========================================
    # 2. LOGIKA PEMROSESAN DATA LAPORAN
    # ==========================================

    # --- A. TRANSAKSI KELUAR ONLY ---
    if jenis_laporan == "Laporan Transaksi Keluar Only":
        st.subheader("📦 Laporan Transaksi Keluar")
        if not df_t.empty and 'Jenis_Transaksi' in df_t.columns:
            df_export = df_t[df_t['Jenis_Transaksi'] == 'Keluar'].copy()
            filename_out = f"Laporan_Transaksi_Keluar_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        else:
            st.info("ℹ️ Tidak ada data transaksi keluar yang ditemukan.")

    # --- B. TRANSAKSI MASUK ONLY ---
    elif jenis_laporan == "Laporan Transaksi Masuk Only":
        st.subheader("📥 Laporan Transaksi Masuk")
        if not df_t.empty and 'Jenis_Transaksi' in df_t.columns:
            df_export = df_t[df_t['Jenis_Transaksi'] == 'Masuk'].copy()
            filename_out = f"Laporan_Transaksi_Masuk_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        else:
            st.info("ℹ️ Tidak ada data transaksi masuk yang ditemukan.")

    # --- C. LAPORAN PERAMALAN TSB ---
    elif jenis_laporan == "Laporan Hasil Peramalan TSB (Terakhir)":
        st.subheader("🔮 Laporan Peramalan TSB & Rekomendasi Restock")
        if not df_ramalan.empty:
            df_export = df_ramalan.copy()
            filename_out = f"Laporan_Hasil_Peramalan_TSB_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        else:
            st.warning("⚠️ Belum ada data hasil peramalan. Silakan buka menu 'Hasil Peramalan' terlebih dahulu untuk melakukan kalkulasi.")

    # ==========================================
    # 3. PREVIEW & TOMBOL UNDUH
    # ==========================================
    if not df_export.empty:
        st.write(f"🔍 **Preview Data ({len(df_export)} Baris):**")
        st.dataframe(df_export, use_container_width=True)
        
        col_d1, col_d2 = st.columns([1, 3])
        with col_d1:
            csv_bytes = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Unduh File CSV",
                data=csv_bytes,
                file_name=filename_out,
                mime="text/csv",
                type="primary",
                use_container_width=True
            )