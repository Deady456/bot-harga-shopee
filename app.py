import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import random
import urllib.parse

st.set_page_config(page_title="Shopee Price Bot", page_icon="🛍️", layout="wide")

def generate_aesthetic_image(product_name, api_key=None):
    if api_key and api_key.strip() != "":
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            payload = {
                "model": "dall-e-3",
                "prompt": f"Aesthetic high quality product photography of {product_name}, clean background, well lit, 4k",
                "n": 1,
                "size": "1024x1024"
            }
            response = requests.post("https://api.openai.com/v1/images/generations", json=payload, headers=headers)
            if response.status_code == 200:
                return response.json()['data'][0]['url']
        except Exception:
            pass 
            
    words = product_name.split()
    keyword = urllib.parse.quote("-".join(words[:2])) if words else "product"
    return f"https://loremflickr.com/400/400/{keyword},product/all"

import os
if os.path.exists("banner.png"):
    st.image("banner.png", use_container_width=True)

st.markdown("### 🛍️ Bot Kalkulator Harga Shopee & AI Image")

st.sidebar.markdown("**⚙️ Pengaturan Global**")
shopee_tax = st.sidebar.number_input("Pajak Shopee (%)", min_value=0.0, max_value=50.0, value=6.5, step=0.1)
packaging_cost = st.sidebar.number_input("Biaya Packaging (Rp)", min_value=0, value=2000, step=500)
profit_margin = st.sidebar.number_input("Target Untung (%)", min_value=0.0, max_value=100.0, value=10.0, step=1.0)
api_key = st.sidebar.text_input("OpenAI API Key (Opsional)", type="password")

tab1, tab2, tab3 = st.tabs(["📄 Upload Banyak (Excel)", "✍️ Input Satuan (Manual)", "🔍 Riset Harga Pasar"])

with tab1:
    col_up1, col_up2 = st.columns([1, 2])
    
    with col_up1:
        st.markdown("**1. Download Template**")
        template_data = pd.DataFrame({"Nama Barang": ["Sepatu Sneakers Pria", "Tas Selempang Wanita"], "Harga Awal": [150000, 85000]})
        towrite = BytesIO()
        template_data.to_excel(towrite, index=False, engine='openpyxl')
        towrite.seek(0)
        st.download_button(label="📥 Download Template", data=towrite, file_name="template.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    
    with col_up2:
        st.markdown("**2. Upload File Anda**")
        uploaded_file = st.file_uploader("Pilih file Excel", type=['xlsx'], label_visibility="collapsed")

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            if 'Nama Barang' not in df.columns or 'Harga Awal' not in df.columns:
                st.error("Error: File Excel harus memiliki kolom 'Nama Barang' dan 'Harga Awal'.")
            else:
                col_btn, col_prev = st.columns([1, 3])
                with col_btn:
                    proses_btn = st.button("🚀 Proses Data", use_container_width=True)
                with col_prev:
                    with st.expander("Lihat Preview Data Awal", expanded=False):
                        st.dataframe(df.head(), height=150)
                
                if proses_btn:
                    with st.spinner('Sedang memproses...'):
                        results = []
                        shopee_tax_rate = shopee_tax / 100.0
                        profit_rate = profit_margin / 100.0
                        
                        for index, row in df.iterrows():
                            nama = row['Nama Barang']
                            harga_awal = float(row['Harga Awal'])
                            
                            divisor = (1 - shopee_tax_rate - profit_rate)
                            harga_jual = 0 if divisor <= 0 else (harga_awal + packaging_cost) / divisor
                            
                            potongan_pajak = harga_jual * shopee_tax_rate
                            profit_nominal = harga_jual * profit_rate
                            image_url = generate_aesthetic_image(nama, api_key)
                            
                            results.append({
                                "Nama Barang": nama,
                                "Harga Awal": harga_awal,
                                "Biaya Packaging": packaging_cost,
                                "Harga Jual": round(harga_jual),
                                "Potongan Shopee": round(potongan_pajak),
                                "Untung Bersih": round(profit_nominal),
                                "URL Gambar": image_url
                            })
                        
                        result_df = pd.DataFrame(results)
                        
                        st.success("✅ Proses selesai!")
                        st.warning("⚠️ Segera download hasilnya! Data ini tidak disimpan secara permanen dan akan hilang jika Anda menutup halaman ini.")
                        
                        col_res1, col_res2 = st.columns([3, 1])
                        with col_res1:
                            st.dataframe(result_df, height=200)
                        with col_res2:
                            output = BytesIO()
                            result_df.to_excel(output, index=False, engine='openpyxl')
                            output.seek(0)
                            st.download_button(label="💾 Download Hasil", data=output, file_name="hasil_shopee.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                            
                        st.markdown("**Preview Gambar Hasil:**")
                        cols = st.columns(min(5, len(result_df)))
                        for i, row in result_df.head(5).iterrows():
                            with cols[i % 5]:
                                st.image(row["URL Gambar"], caption=row["Nama Barang"], use_column_width=True)
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")

with tab2:
    col_input, col_output = st.columns([1, 1])
    
    with col_input:
        with st.form("single_item_form"):
            st.markdown("**Masukkan Detail Barang**")
            nama_barang = st.text_input("Nama Barang", placeholder="Kemeja Flanel")
            harga_awal = st.number_input("Harga Modal (Rp)", min_value=0, value=50000, step=5000)
            st.markdown("Upload Foto (Opsional)")
            foto_barang = st.file_uploader("Upload Foto Asli", type=['jpg', 'jpeg', 'png'], label_visibility="collapsed")
            submit_button = st.form_submit_button("🚀 Hitung & Generate", use_container_width=True)
            
    with col_output:
        if submit_button:
            if not nama_barang:
                st.warning("Masukkan nama barang.")
            else:
                with st.spinner('Memproses...'):
                    shopee_tax_rate = shopee_tax / 100.0
                    profit_rate = profit_margin / 100.0
                    
                    divisor = (1 - shopee_tax_rate - profit_rate)
                    harga_jual = 0 if divisor <= 0 else (harga_awal + packaging_cost) / divisor
                    
                    potongan_pajak = harga_jual * shopee_tax_rate
                    profit_nominal = harga_jual * profit_rate
                    image_url = generate_aesthetic_image(nama_barang, api_key)
                    
                    st.success("✅ Selesai!")
                    col_r1, col_r2 = st.columns([1, 1])
                    with col_r1:
                        st.markdown(f"**{nama_barang}**")
                        st.caption(f"Modal: Rp {harga_awal:,.0f} | Pack: Rp {packaging_cost:,.0f}")
                        st.markdown(f"### Jual: Rp {harga_jual:,.0f}")
                        st.caption(f"Pajak ({shopee_tax}%): Rp {potongan_pajak:,.0f}")
                        st.caption(f"Untung ({profit_margin}%): Rp {profit_nominal:,.0f}")
                    with col_r2:
                        st.image(image_url, use_column_width=True)
                        st.markdown(f"[Buka Gambar]({image_url})")
                        
                    # Tambahan Export ke Excel untuk satuan
                    single_result_df = pd.DataFrame([{
                        "Nama Barang": nama_barang,
                        "Harga Awal": harga_awal,
                        "Biaya Packaging": packaging_cost,
                        "Harga Jual": round(harga_jual),
                        "Potongan Shopee": round(potongan_pajak),
                        "Untung Bersih": round(profit_nominal),
                        "URL Gambar": image_url
                    }])
                    
                    output_single = BytesIO()
                    single_result_df.to_excel(output_single, index=False, engine='openpyxl')
                    output_single.seek(0)
                    st.markdown("---")
                    st.warning("⚠️ Segera export hasilnya! Data ini akan hilang jika halaman dimuat ulang.")
                    st.download_button(
                        label="💾 Export Hasil ini ke Excel", 
                        data=output_single, 
                        file_name=f"harga_{nama_barang.replace(' ', '_')}.xlsx", 
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                        use_container_width=True
                    )
        else:
            st.info("👈 Isi form di samping lalu klik Hitung untuk melihat hasil di sini.")

with tab3:
    st.markdown("### 🔍 Riset Harga Pasar (Kompetitor)")
    st.markdown("Cari data produk ini di berbagai online shop (katalog/marketplace) untuk membandingkan harga pasar sebelum Anda menetapkan harga jual akhir.")
    
    with st.form("research_form"):
        col_res1, col_res2 = st.columns([3, 1])
        with col_res1:
            search_query = st.text_input("Nama Barang yang Ingin Diriset", placeholder="Contoh: Sepatu Sneakers Pria")
        with col_res2:
            st.markdown("<br>", unsafe_allow_html=True) # Spacer
            btn_search = st.form_submit_button("Cari Data Sumber", use_container_width=True)
        
    if btn_search:
        if not search_query:
            st.warning("Masukkan nama barang untuk diriset.")
        else:
            q_url = urllib.parse.quote(search_query)
            shopee_url = f"https://shopee.co.id/search?keyword={q_url}"
            tokped_url = f"https://www.tokopedia.com/search?q={q_url}"
            lazada_url = f"https://www.lazada.co.id/catalog/?q={q_url}"
            google_url = f"https://www.google.com/search?tbm=shop&q={q_url}"
            
            st.success(f"Berhasil! Klik tombol di bawah untuk melihat harga rata-rata dari kompetitor untuk **{search_query}**:")
            
            col_link1, col_link2, col_link3, col_link4 = st.columns(4)
            with col_link1:
                st.link_button("🛒 Cari di Shopee", shopee_url, use_container_width=True)
            with col_link2:
                st.link_button("🛒 Cari di Tokopedia", tokped_url, use_container_width=True)
            with col_link3:
                st.link_button("🛒 Cari di Lazada", lazada_url, use_container_width=True)
            with col_link4:
                st.link_button("🌐 Google Shopping", google_url, use_container_width=True)
            
            st.info("💡 **Tips:** Perhatikan harga jual mereka, lalu kembali ke **Tab Input Satuan** untuk mengatur modal dan memastikan harga jual bot kita tetap bersaing!")
