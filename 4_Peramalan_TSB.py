import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils import check_login, init_session_state, hitung_tsb_lengkap, simpan_ke_db

init_session_state()
# KUNCI HAK AKSES: Hanya Admin Purchasing yang bisa mengakses
check_login(allowed_roles=["Admin Purchasing"])

st.header("⭐ Mesin Peramalan Teunter-Syntetos-Babai (TSB)")
st.info("💡 **Catatan:** Metode peramalan TSB hanya menghitung data berdasarkan **Transaksi Keluar** (Permintaan/Penjualan).")

df_t = st.session_state['df_transaksi']

df_keluar = df_t[df_t['Jenis_Transaksi'] == 'Keluar'] if not df_t.empty and 'Jenis_Transaksi' in df_t.columns else pd.DataFrame()
list_barang_transaksi = df_keluar['ID_Barang'].unique() if not df_keluar.empty else []

if len(list_barang_transaksi) == 0:
    st.error("🚨 Data transaksi 'Keluar' historis masih kosong. Sistem membutuhkan riwayat penjualan untuk peramalan.")
    st.stop()

with st.form("form_tsb"):
    c1, c2 = st.columns(2)
    with c1:
        pilih_barang = st.selectbox("Pilih Barang", list_barang_transaksi)
        periode = st.number_input("Periode Ramalan (Bulan ke Depan)", min_value=1, value=1)
    with c2:
        alpha = st.slider("Alpha (α) - Parameter Magnitude", 0.01, 0.99, 0.20)
        beta = st.slider("Beta (β) - Parameter Probabilitas", 0.01, 0.99, 0.15)
        
    if st.form_submit_button("🚀 Hitung Peramalan", use_container_width=True):
        data_hist = df_keluar[df_keluar['ID_Barang'] == pilih_barang].sort_values(by='Tanggal')
        y = data_hist['Qty'].values
        waktu = data_hist['Tanggal'].dt.strftime('%Y-%m').tolist()
        
        if len(y) < 2:
            st.error("Data historis (penjualan) barang ini tidak mencukupi. TSB membutuhkan minimal 2 catatan transaksi.")
        else:
            z, p, fitted, forecast_next, mad, mse = hitung_tsb_lengkap(y, alpha, beta)
            
            new_pred = pd.DataFrame({
                'Waktu_Hitung': [datetime.now().strftime("%Y-%m-%d %H:%M")],
                'ID_Barang': [pilih_barang],
                'Periode_Ramalan': [f"{periode} Bulan"],
                'Ramalan_Qty': [round(forecast_next * periode, 2)],
                'MAD': [round(mad, 2)],
                'MSE': [round(mse, 2)]
            })
            st.session_state['df_peramalan'] = pd.concat([st.session_state['df_peramalan'], new_pred], ignore_index=True)
            
            simpan_ke_db()
            
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(f"Peramalan ({periode} Bulan)", f"{forecast_next * periode:.2f} Unit")
            m2.metric(r"Demand Size ($Z_t$)", f"{z[-1]:.2f}")
            m3.metric(r"Probabilitas ($P_t$)", f"{p[-1]:.2f}")
            m4.metric("Error (MSE)", f"{mse:.2f}")
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=waktu, y=y, name='Penjualan Aktual (Intermittent)', marker_color='#ef553b'))
            fig.add_trace(go.Scatter(x=waktu, y=fitted, mode='lines+markers', name='Fitted Value TSB', line=dict(color='#00cc96', width=2)))
            fig.update_layout(title=f"Grafik Historis Penjualan vs Penghalusan TSB ({pilih_barang})", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)