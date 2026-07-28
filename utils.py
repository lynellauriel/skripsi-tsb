import streamlit as st
import pandas as pd
import numpy as np
import hashlib
import sqlite3
import os

DB_NAME = 'database_skripsi.db'

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def get_db_conn():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS list_barang (ID_Barang TEXT PRIMARY KEY, Nama_Barang TEXT, Kategori TEXT, Stok_Saat_Ini INTEGER, Safety_Stock INTEGER, Spesifikasi TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transaksi (ID_Transaksi TEXT PRIMARY KEY, Tanggal TEXT, ID_Barang TEXT, Jenis_Transaksi TEXT, Qty_Transaksi INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS peramalan (Waktu_Hitung TEXT, ID_Barang TEXT, Periode_Ramalan TEXT, Ramalan_Qty REAL, MAD REAL, MSE REAL)''')
    conn.commit()
    conn.close()

def load_data_from_db():
    conn = get_db_conn()
    st.session_state['df_barang'] = pd.read_sql("SELECT * FROM list_barang", conn)
    
    df_trx = pd.read_sql("SELECT * FROM transaksi", conn)
    if not df_trx.empty:
        df_trx['Tanggal'] = pd.to_datetime(df_trx['Tanggal'])
    st.session_state['df_transaksi'] = df_trx
    
    st.session_state['df_peramalan'] = pd.read_sql("SELECT * FROM peramalan", conn)
    conn.close()

def simpan_ke_db():
    conn = get_db_conn()
    st.session_state['df_barang'].to_sql('list_barang', conn, if_exists='replace', index=False)
    
    df_trx = st.session_state['df_transaksi'].copy()
    if not df_trx.empty:
        df_trx['Tanggal'] = df_trx['Tanggal'].astype(str)
    df_trx.to_sql('transaksi', conn, if_exists='replace', index=False)
    
    st.session_state['df_peramalan'].to_sql('peramalan', conn, if_exists='replace', index=False)
    conn.close()

def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        st.session_state['user_role'] = ''
        
    if not os.path.exists(DB_NAME):
        init_db()
        
    if 'df_barang' not in st.session_state:
        load_data_from_db()
        
    if 'df_transaksi' not in st.session_state or st.session_state['df_transaksi'].empty:
        st.session_state['df_transaksi'] = pd.DataFrame(columns=['ID_Transaksi', 'Tanggal', 'ID_Barang', 'Jenis_Transaksi', 'Qty'])

def render_sidebar_app():
    with st.sidebar:
        st.title("Sistem Peramalan")
        st.caption("Sistem Peramalan menggunakan Metode TSB")
        st.markdown("---")
        
        if st.session_state.get('logged_in', False):
            st.success(f"👤 **{st.session_state['username']}**\n\nRole: *{st.session_state['user_role']}*")
            if st.button("🚪 Logout / Keluar", use_container_width=True, type="secondary"):
                st.session_state['logged_in'] = False
                st.session_state['username'] = ''
                st.session_state['user_role'] = ''
                st.rerun()
        else:
            st.warning("🔒 Anda belum login")
        
        st.markdown("---")
        st.caption("© 2026 Skripsi TI - TSB Forecasting")

def hitung_tsb_lengkap(y, alpha, beta):
    n = len(y)
    z = np.zeros(n)
    p = np.zeros(n)
    
    z[0] = y[0] if y[0] > 0 else (y[y > 0][0] if len(y[y > 0]) > 0 else 1)
    p[0] = 1.0 if y[0] > 0 else 0.5
    
    for t in range(1, n):
        if y[t] > 0:
            z[t] = z[t-1] + alpha * (y[t] - z[t-1])
            p[t] = p[t-1] + beta * (1.0 - p[t-1])
        else:
            z[t] = z[t-1]
            p[t] = p[t-1] + beta * (0.0 - p[t-1])
            
    fitted = z * p
    forecast_next = z[-1] * p[-1]
    
    error = y - fitted
    mad = np.mean(np.abs(error))
    mse = np.mean(error**2)
    
    return z, p, fitted, forecast_next, mad, mse

def check_login(allowed_roles=None):
    """Memeriksa status login dan hak akses role user"""
    render_sidebar_app()
    if not st.session_state.get('logged_in', False):
        st.warning("🔒 Akses Ditolak. Silakan login melalui halaman Utama/App.")
        st.stop()
        
    if allowed_roles:
        user_role = st.session_state.get('user_role', '')
        if user_role not in allowed_roles:
            st.error(f"⛔ **Akses Ditolak!** Halaman ini khusus untuk role: **{', '.join(allowed_roles)}**.")
            st.info(f"Role Anda saat ini adalah: **{user_role}**")
            st.stop()

def is_role_allowed(allowed_roles):
    """
    Mengecek apakah role user saat ini ada di dalam list allowed_roles.
    Returns: True jika diizinkan, False jika tidak.
    """
    current_role = str(st.session_state.get("role", "")).strip().lower()
    allowed_roles_clean = [r.strip().lower() for r in allowed_roles]
    
    return current_role in allowed_roles_clean