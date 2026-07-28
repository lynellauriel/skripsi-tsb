import streamlit as st
import pandas as pd
from utils import check_login, init_session_state, simpan_ke_db

init_session_state()
check_login(allowed_roles=["Admin Gudang"])

@st.dialog("⚠️ Konfirmasi Hapus Data Barang")
def dialog_hapus_barang(id_barang):
    st.warning(f"Apakah Anda yakin ingin menghapus barang **{id_barang}**?")
    st.caption("🚨 Tindakan ini tidak dapat dibatalkan dan akan menghapus data dari database.")
    col1, col2 = st.columns(2)
    if col1.button("Ya, Hapus Data", type="primary", use_container_width=True):
        st.session_state['df_barang'] = st.session_state['df_barang'][st.session_state['df_barang']['ID_Barang'] != id_barang].reset_index(drop=True)
        simpan_ke_db()
        st.toast(f"Data {id_barang} berhasil dihapus!", icon="🗑️")
        st.rerun()
    if col2.button("Batal", use_container_width=True):
        st.rerun()

st.header("📦 Kelola Master Data Barang")

#if is_role_allowed(["Admin Gudang"]):
tab1, tab2, tab3 = st.tabs(["📋 Lihat Data", "➕ Tambah Data", "✏️ Update / Hapus Data"])
#else:
    #tab1, = st.tabs(["📋 Lihat Data"])

with tab1:
    if st.session_state['df_barang'].empty:
        st.warning("Data Master Barang masih kosong.")
    else:
        st.dataframe(st.session_state['df_barang'], use_container_width=True)

#if is_role_allowed(["Admin Gudang"]):
with tab2:
    with st.form("form_create_barang"):
        id_b = st.text_input("ID Barang Baru (Contoh: PMP-001)")
        nama_b = st.text_input("Nama Barang")
        kat_b = st.selectbox("Kategori", ["Pompa Air", "Peralatan Pemadam", "Suku Cadang", "Aksesoris"])
        stok_b = st.number_input("Stok Awal", min_value=0)
        ss_b = st.number_input("Safety Stock (Batas Aman)", min_value=0)
            
        if not id_b or not nama_b:
            st.error("ID dan Nama Barang tidak boleh kosong!")
        elif id_b in st.session_state['df_barang']['ID_Barang'].values:
            st.error("ID Barang sudah terdaftar!")
        else:
            new_row = pd.DataFrame({'ID_Barang': [id_b], 'Nama_Barang': [nama_b], 'Kategori': [kat_b], 'Stok_Saat_Ini': [stok_b], 'Safety_Stock': [ss_b]})
            st.session_state['df_barang'] = pd.concat([st.session_state['df_barang'], new_row], ignore_index=True)
                
                # SIMPAN KE DATABASE
            simpan_ke_db()
            st.success("Data berhasil ditambahkan dan disimpan permanen!")

with tab3:
    df = st.session_state['df_barang']
    if df.empty:
        st.info("Belum ada data untuk diubah atau dihapus.")
    else:
        selected_id = st.selectbox("Pilih ID Barang untuk Dikelola", df['ID_Barang'].tolist())
            
        if selected_id:
            current_data = df[df['ID_Barang'] == selected_id].iloc[0]
            with st.form("form_update_barang"):
                kategori_list = ["Pompa Air", "Peralatan Pemadam", "Suku Cadang", "Aksesoris"]
                current_kat_idx = kategori_list.index(current_data['Kategori']) if current_data['Kategori'] in kategori_list else 0
                    
                u_nama = st.text_input("Nama Barang", value=current_data['Nama_Barang'])
                u_kat = st.selectbox("Kategori", kategori_list, index=current_kat_idx)
                u_stok = st.number_input("Stok Saat Ini", min_value=0, value=int(current_data['Stok_Saat_Ini']))
                u_ss = st.number_input("Safety Stock", min_value=0, value=int(current_data['Safety_Stock']))
                    
                c_up, c_del = st.columns(2)
                btn_update = c_up.form_submit_button("Simpan Perubahan", type="primary")
                btn_delete = c_del.form_submit_button("Hapus Data")
                
                if btn_update:
                    idx = df.index[df['ID_Barang'] == selected_id].tolist()[0]
                    st.session_state['df_barang'].at[idx, 'Nama_Barang'] = u_nama
                    st.session_state['df_barang'].at[idx, 'Kategori'] = u_kat
                    st.session_state['df_barang'].at[idx, 'Stok_Saat_Ini'] = u_stok
                    st.session_state['df_barang'].at[idx, 'Safety_Stock'] = u_ss
                        
                        # SIMPAN KE DATABASE
                    simpan_ke_db()
                    st.success("Data berhasil diperbarui!")
                    st.rerun()
                        
                if btn_delete:
                    st.session_state['df_barang'] = df[df['ID_Barang'] != selected_id].reset_index(drop=True)
                        
                        # SIMPAN KE DATABASE
                    simpan_ke_db()
                    st.warning(f"Data {selected_id} berhasil dihapus!")
                    st.rerun()