import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from utils import check_login, init_session_state, simpan_ke_db

init_session_state()
check_login()

# Inisialisasi DataFrame Riwayat Ramalan di Session State
if 'df_riwayat_ramalan' not in st.session_state:
    st.session_state['df_riwayat_ramalan'] = pd.DataFrame(columns=[
        'Waktu_Hitung', 'ID_Barang', 'Nama_Barang', 'Alpha', 'Omega', 
        'Ramalan_Demand_TSB', 'Status_Ramalan', 'Qty_Order'
    ])

st.header("📄 Hasil Peramalan TSB & Rekomendasi Restock")

# Validasi ketersediaan data master barang
if 'df_barang' not in st.session_state or st.session_state['df_barang'].empty:
    st.warning("⚠️ Data Master Barang masih kosong. Silakan isi data barang terlebih dahulu.")
    st.stop()

df_b = st.session_state['df_barang'].copy()
df_t = st.session_state.get('df_transaksi', pd.DataFrame()).copy()

# ==========================================
# FUNGSI PERAMALAN TSB (INTERMITTENT DEMAND)
# ==========================================
def hitung_tsb(series_demand, alpha=0.2, omega=0.2):
    n = len(series_demand)
    if n == 0:
        return 0.0, np.array([]), np.array([])
    
    z = np.zeros(n)
    p = np.zeros(n)
    y = np.zeros(n)
    
    first_non_zero = np.where(series_demand > 0)[0]
    if len(first_non_zero) == 0:
        return 0.0, np.zeros(n), np.zeros(n)
    
    init_idx = first_non_zero[0]
    z_curr = series_demand[init_idx]
    p_curr = 1.0 / (init_idx + 1)
    
    for t in range(n):
        d_t = series_demand[t]
        if d_t > 0:
            z_curr = alpha * d_t + (1 - alpha) * z_curr
            p_curr = omega * 1.0 + (1 - omega) * p_curr
        else:
            p_curr = (1 - omega) * p_curr
        
        z[t] = z_curr
        p[t] = p_curr
        y[t] = z_curr * p_curr
        
    next_forecast = z_curr * p_curr
    return round(next_forecast, 2), y, series_demand

# ==========================================
# SIDEBAR PARAMETER
# ==========================================
st.sidebar.subheader("⚙️ Parameter TSB")
alpha = st.sidebar.number_input("Alpha (Smoothing Demand Size)", min_value=0.01, max_value=1.00, value=0.20, step=0.01, format="%.2f")
omega = st.sidebar.number_input("Omega (Smoothing Demand Probability)", min_value=0.01, max_value=1.00, value=0.20, step=0.01, format="%.2f")

# ==========================================
# PROSES KALKULASI HANYA PADA BARANG DENGAN RIWAYAT
# ==========================================
results = []
historical_chart_data = {}

for _, row in df_b.iterrows():
    id_b = row['ID_Barang']
    nama_b = row['Nama_Barang']
    stok_curr = int(row['Stok_Saat_Ini'])
    ss = int(row['Safety_Stock'])
    
    sudah_dihitung = False
    forecast_next = 0.0
    
    if not df_t.empty and 'ID_Barang' in df_t.columns and 'Jenis_Transaksi' in df_t.columns:
        trx_keluar = df_t[(df_t['ID_Barang'] == id_b) & (df_t['Jenis_Transaksi'] == 'Keluar')].copy()
        if not trx_keluar.empty:
            sudah_dihitung = True
            trx_keluar['Tanggal'] = pd.to_datetime(trx_keluar['Tanggal'])
            ts_demand = trx_keluar.groupby('Tanggal')['Qty'].sum().sort_index()
            demand_series = ts_demand.values
            
            forecast_next, y_hist, d_hist = hitung_tsb(demand_series, alpha, omega)
            
            historical_chart_data[id_b] = {
                'dates': ts_demand.index.strftime('%Y-%m-%d').tolist(),
                'demand': d_hist.tolist(),
                'forecast_hist': y_hist.tolist()
            }
    
    if sudah_dihitung:
        if stok_curr <= ss or stok_curr < forecast_next:
            status_ramalan = "Order Now (Full-Container)"
            qty_order = 30
        else:
            status_ramalan = "Hold Order"
            qty_order = 0
            
        results.append({
            'ID_Barang': id_b,
            'Nama_Barang': nama_b,
            'Merk_Barang': row.get('Merk_Barang', '-'),
            'Stok_Saat_Ini': stok_curr,
            'Safety_Stock': ss,
            'Alpha': alpha,
            'Omega': omega,
            'Ramalan_Demand_TSB': forecast_next,
            'Status_Ramalan': status_ramalan,
            'Qty_Order': qty_order
        })

df_res = pd.DataFrame(results)
# Simpan df_res ke session_state agar bisa langsung ditarik di menu Laporan
st.session_state['df_hasil_ramalan_terakhir'] = df_res

# ==========================================
# TAMPILAN HASIL PERAMALAN
# ==========================================
if df_res.empty:
    st.info("ℹ️ Belum ada barang yang memiliki riwayat transaksi 'Keluar' untuk dihitung ramalannya.")
else:
    st.subheader("📊 Indikator Ringkasan Hasil Peramalan")
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    total_items = len(df_res)
    order_now_count = len(df_res[df_res['Status_Ramalan'] == 'Order Now (Full-Container)'])
    hold_count = len(df_res[df_res['Status_Ramalan'] == 'Hold Order'])
    total_qty_reorder = df_res['Qty_Order'].sum()

    col_m1.metric(label="Barang Dihitung Ramalannya", value=f"{total_items} Items")
    col_m2.metric(label="🚨 Order Now (Full-Container)", value=f"{order_now_count} Items", delta=f"{order_now_count} perlu restock", delta_color="inverse")
    col_m3.metric(label="⏸️ Hold Order", value=f"{hold_count} Items", delta=f"{hold_count} stok aman")
    col_m4.metric(label="📦 Total Qty Order", value=f"{total_qty_reorder} Unit")

    st.markdown("---")

    st.subheader("📋 Tabel Rekomendasi Status Ramalan & Order")

    def highlight_status(val):
        if val == "Order Now (Full-Container)":
            return 'background-color: #ff4b4b; color: white; font-weight: bold;'
        elif val == "Hold Order":
            return 'background-color: #1c83e1; color: white;'
        return ''

    st.dataframe(
        df_res.style.map(highlight_status, subset=['Status_Ramalan']),
        use_container_width=True
    )

    st.markdown("---")

    st.subheader("📈 Visualisasi Fluktuasi Demand Intermittent & Tren TSB")

    pilihan_barang = st.selectbox(
        "Pilih Barang untuk Menampilkan Grafik Fluktuasi:",
        options=df_res['ID_Barang'].tolist(),
        format_func=lambda x: f"{x} - {df_res[df_res['ID_Barang'] == x]['Nama_Barang'].values[0]}"
    )

    if pilihan_barang in historical_chart_data and len(historical_chart_data[pilihan_barang]['demand']) > 0:
        data_pilihan = historical_chart_data[pilihan_barang]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=data_pilihan['dates'],
            y=data_pilihan['demand'],
            name='Permintaan Aktual (Intermittent)',
            marker_color='rgba(239, 85, 59, 0.7)'
        ))
        fig.add_trace(go.Scatter(
            x=data_pilihan['dates'],
            y=data_pilihan['forecast_hist'],
            mode='lines+markers',
            name='Hasil Smoothing TSB',
            line=dict(color='#00CC96', width=3)
        ))
        fig.update_layout(
            title=f"Grafik Fluktuasi Demand Intermittent vs Tren TSB ({pilihan_barang})",
            xaxis_title="Tanggal Transaksi",
            yaxis_title="Jumlah Demand (Qty)",
            hovermode="x unified",
            template="plotly_white",
            height=450
        )
        st.plotly_chart(fig, use_container_width=True)
