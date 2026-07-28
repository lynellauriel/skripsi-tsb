import streamlit as st
import pandas as pd
from utils import check_login, init_session_state, simpan_ke_db

init_session_state()
check_login(allowed_roles=["Admin Gudang"])


st.header("🛒 Kelola Data Transaksi (Masuk & Keluar)")

@st.dialog("⚠️ Konfirmasi Hapus Transaksi")
def dialog_hapus_transaksi(id_trx, id_barang, jenis_trx, qty):
    st.warning(f"Apakah Anda yakin ingin menghapus transaksi **{id_trx}**?")
    st.caption("🔄 Stok pada Daftar Barang terkait akan otomatis dikembalikan (di-undo) ke posisi semula.")
    col1, col2 = st.columns(2)
    if col1.button("Ya, Hapus Transaksi", type="primary", use_container_width=True):
        # Revert/Undo Stok
        update_stok_barang(id_barang, jenis_trx, qty, is_revert=True)
        # Hapus Baris Transaksi
        st.session_state['df_transaksi'] = st.session_state['df_transaksi'][st.session_state['df_transaksi']['ID_Transaksi'] != id_trx].reset_index(drop=True)
        simpan_ke_db()
        st.toast(f"Transaksi {id_trx} berhasil dihapus dan stok disesuaikan!", icon="🗑️")
        st.rerun()
    if col2.button("Batal", use_container_width=True):
        st.rerun()

#if is_role_allowed(["Admin Gudang"]):
tab_riwayat, tab_manual, tab_upload = st.tabs(["📋 Riwayat Transaksi & Kelola", "➕ Input Manual Transaksi", "📥 Upload Batch (CSV/Excel)"])
#else:
#    tab_riwayat, = st.tabs(["📋 Data Riwayat Transaksi"])

df_trx = st.session_state['df_transaksi']
list_barang = st.session_state['df_barang']['ID_Barang'].tolist()

def update_stok_barang(id_barang, jenis_trx, qty, is_revert=False):
    idx_b = st.session_state['df_barang'].index[st.session_state['df_barang']['ID_Barang'] == id_barang].tolist()
    if idx_b:
        idx = idx_b[0]
        multiplier = -1 if is_revert else 1
        if jenis_trx == 'Masuk':
            st.session_state['df_barang'].at[idx, 'Stok_Saat_Ini'] += (qty * multiplier)
        elif jenis_trx == 'Keluar':
            st.session_state['df_barang'].at[idx, 'Stok_Saat_Ini'] -= (qty * multiplier)

# TAB 1: RIWAYAT TRANSAKSI
with tab_riwayat:
    if df_trx.empty:
        st.info("Riwayat transaksi masih kosong. Silakan input manual atau upload batch.")
    else:
        st.subheader("Daftar Riwayat Transaksi (Masuk & Keluar)")
        st.dataframe(df_trx.sort_values(by='Tanggal', ascending=False), use_container_width=True)
        
        st.markdown("---")
        
        st.subheader("Edit / Hapus Transaksi")
        selected_trx = st.selectbox("Pilih ID Transaksi", df_trx['ID_Transaksi'].tolist())
        if selected_trx:
            curr_trx = df_trx[df_trx['ID_Transaksi'] == selected_trx].iloc[0]
            with st.form("form_update_trx"):
                u_tgl = st.date_input("Tanggal", value=pd.to_datetime(curr_trx['Tanggal']))
                idx_b = list_barang.index(curr_trx['ID_Barang']) if curr_trx['ID_Barang'] in list_barang else 0
                u_idb = st.selectbox("ID Barang", list_barang, index=idx_b)
                idx_j = ["Masuk", "Keluar"].index(curr_trx['Jenis_Transaksi']) if curr_trx['Jenis_Transaksi'] in ["Masuk", "Keluar"] else 0
                u_jenis = st.selectbox("Jenis Transaksi", ["Masuk", "Keluar"], index=idx_j)
                u_qty = st.number_input("Kuantitas (Qty)", min_value=1, value=int(curr_trx['Qty']))
                    
                c1, c2 = st.columns(2)
                if c1.form_submit_button("Update", type="primary"):
                    # 1. Revert stok dari transaksi lama
                    update_stok_barang(curr_trx['ID_Barang'], curr_trx['Jenis_Transaksi'], curr_trx['Qty'], is_revert=True)
                    # 2. Tambah stok dengan transaksi baru
                    update_stok_barang(u_idb, u_jenis, u_qty)
                        
                    idx = df_trx.index[df_trx['ID_Transaksi'] == selected_trx].tolist()[0]
                    st.session_state['df_transaksi'].at[idx, 'Tanggal'] = pd.to_datetime(u_tgl)
                    st.session_state['df_transaksi'].at[idx, 'ID_Barang'] = u_idb
                    st.session_state['df_transaksi'].at[idx, 'Jenis_Transaksi'] = u_jenis
                    st.session_state['df_transaksi'].at[idx, 'Qty'] = u_qty
                        
                    simpan_ke_db()
                    st.success("Data diperbarui dan stok disesuaikan!")
                    st.rerun()
                        
                if c2.form_submit_button("Hapus"):
                    # Kembalikan stok karena transaksi batal
                    update_stok_barang(curr_trx['ID_Barang'], curr_trx['Jenis_Transaksi'], curr_trx['Qty'], is_revert=True)
                        
                    st.session_state['df_transaksi'] = df_trx[df_trx['ID_Transaksi'] != selected_trx].reset_index(drop=True)
                    simpan_ke_db()
                    st.warning("Transaksi dihapus dan stok dikembalikan ke semula!")
                    st.rerun()
        
#if is_role_allowed(["Admin Gudang"]):
# TAB 2: INPUT MANUAL
with tab_manual:
    if not list_barang:
        st.warning("Data Barang masih kosong! Tambahkan barang di menu Daftar Barang terlebih dahulu.")
    else:
        with st.form("form_input_trx_manual"):
            m_tgl = st.date_input("Tanggal Transaksi")
            m_idb = st.selectbox("Pilih Barang", list_barang)
            m_jenis = st.selectbox("Jenis Transaksi", ["Masuk", "Keluar"])
            m_qty = st.number_input("Kuantitas (Qty)", min_value=1)
            
            if st.form_submit_button("Simpan Transaksi", type="primary"):
                new_id = f"TRX-{len(st.session_state['df_transaksi']) + 1:03d}"
                new_trx = pd.DataFrame({'ID_Transaksi': [new_id], 'Tanggal': [pd.to_datetime(m_tgl)], 'ID_Barang': [m_idb], 'Jenis_Transaksi': [m_jenis], 'Qty': [m_qty]})
                
                update_stok_barang(m_idb, m_jenis, m_qty)
                st.session_state['df_transaksi'] = pd.concat([st.session_state['df_transaksi'], new_trx], ignore_index=True)
                simpan_ke_db()
                    
                st.toast(f"✅ Transaksi {new_id} berhasil disimpan!", icon="🎉")
                st.rerun() # REFRESH SUPAYA Halaman Riwayat & Stok Langsung Terupdate!

# TAB 3: UPLOAD BATCH CSV / EXCEL
with tab_upload:
    uploaded_file = st.file_uploader("Upload Transaksi Penjualan / Masuk (CSV atau Excel)", type=['csv', 'xlsx', 'xls'])
    st.caption("Persyaratan Kolom: `ID_Transaksi`, `Tanggal`, `ID_Barang`, `Jenis_Transaksi`, `Qty`")
        
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_new = pd.read_csv(uploaded_file)
            else:
                df_new = pd.read_excel(uploaded_file)
                    
            req_cols = {'ID_Transaksi', 'Tanggal', 'ID_Barang', 'Jenis_Transaksi', 'Qty'}
            if req_cols.issubset(df_new.columns):
                df_new['Tanggal'] = pd.to_datetime(df_new['Tanggal'])
                    
                for _, row in df_new.iterrows():
                    update_stok_barang(row['ID_Barang'], row['Jenis_Transaksi'], row['Qty'])
                        
                st.session_state['df_transaksi'] = pd.concat([st.session_state['df_transaksi'], df_new], ignore_index=True)
                simpan_ke_db()
                st.toast("✅ File berhasil diunggah!", icon="🎉")
                st.rerun()
            else:
                st.error(f"Format kolom tidak sesuai. Wajib mencakup: {req_cols}")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca file: {e}")
