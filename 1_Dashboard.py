import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import init_session_state, render_sidebar_app, make_hash

st.set_page_config(page_title="Sistem Peramalan TSB", layout="wide", page_icon="📦")
init_session_state()

# Database User Sederhana
USERS = {
    "admingudang": {"password": make_hash("gudang123"), "role": "Admin Gudang"},
    "adminpurchasing": {"password": make_hash("purchasing123"), "role": "Admin Purchasing"}
}

render_sidebar_app()

if not st.session_state.get('logged_in', False):
    st.header("🔑 Login Sistem Peramalan TSB")
    with st.form("form_login"):
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Masuk Ke Sistem", type="primary"):
            hashed_pwd = make_hash(pwd)
            if user in USERS and USERS[user]["password"] == hashed_pwd:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user
                st.session_state['user_role'] = USERS[user]["role"]
                st.success("Login Berhasil!")
                st.rerun()
            else:
                st.error("Username atau Password salah!")
else:
    st.header("📊 Dashboard Utama Sistem")
    df_b = st.session_state['df_barang']
    df_t = st.session_state['df_transaksi']

    if not df_b.empty:
        stok_kritis = df_b[df_b['Stok_Saat_Ini'] < df_b['Safety_Stock']]
        if not stok_kritis.empty:
            for _, row in stok_kritis.iterrows():
                st.error(f"⚠️ **PERINGATAN:** Stok **{row['Nama_Barang']}** menipis! (Sisa: {row['Stok_Saat_Ini']}, Minimum: {row['Safety_Stock']})")

    df_keluar = df_t[df_t['Jenis_Transaksi'] == 'Keluar'] if not df_t.empty and 'Jenis_Transaksi' in df_t.columns else pd.DataFrame()
    item_terlaris = df_keluar['ID_Barang'].mode()[0] if not df_keluar.empty else "-"

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Daftar Barang", len(df_b))
    c2.metric("Total Transaksi Recorded", len(df_t))
    c3.metric("Item Terlaris (Keluar)", item_terlaris)

    st.markdown("---")
    if df_b.empty:
        st.info("Visualisasi grafik belum tersedia. Silakan input Daftar Barang terlebih dahulu.")
    else:
        fig = go.Figure(data=[
            go.Bar(name='Stok Aktual', x=df_b['Nama_Barang'], y=df_b['Stok_Saat_Ini'], marker_color='#1f77b4'),
            go.Bar(name='Safety Stock', x=df_b['Nama_Barang'], y=df_b['Safety_Stock'], marker_color='#ff7f0e')
        ])
        fig.update_layout(title="Visualisasi Stok vs Batas Aman (Safety Stock)", barmode='group', template='plotly_white')
        st.plotly_chart(fig, use_container_width=True)