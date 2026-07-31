"""
app.py
Aplikasi utama Streamlit.

STUDI KASUS TUNGGAL: Sistem Informasi Katalog Buku
- Data dasar (judul, harga, rating, stok)  -> hasil WEB SCRAPING dari books.toscrape.com
- Data pelengkap (penulis, tahun, subjek)   -> hasil TARIK API dari Open Library

Kedua sumber data disatukan dalam SATU tampilan katalog buku (join dua tabel),
bukan ditampilkan sebagai dua fitur yang terpisah.
"""

import streamlit as st
import pandas as pd

import db
import scraper
import api_client

st.set_page_config(page_title="Sistem Informasi Katalog Buku", layout="wide")

db.init_db()

st.title("📚 Sistem Informasi Katalog Buku")
st.caption(
    "Data dasar buku diambil lewat **Web Scraping** (books.toscrape.com), "
    "lalu dilengkapi lewat **API** (Open Library) — keduanya menyatu dalam satu katalog."
)

# ---------------------------------------------------------------------
# 1. Ambil data baru
# ---------------------------------------------------------------------
with st.expander("🔄 Ambil Data Baru", expanded=False):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Langkah 1: Scraping data dasar buku**")
        pages = st.number_input("Jumlah halaman yang di-scrape", min_value=1, max_value=10, value=1)
        if st.button("Scrape Buku Baru"):
            with st.spinner("Mengambil data dari books.toscrape.com..."):
                jumlah = scraper.scrape_books(pages=pages)
            st.success(f"{jumlah} buku baru berhasil disimpan.")
            st.rerun()

    with col2:
        st.markdown("**Langkah 2: Lengkapi buku lewat API**")
        st.write("Pilih buku di tabel bawah, lalu klik tombol *Ambil Detail dari API*.")

# ---------------------------------------------------------------------
# 2. Tambah buku manual (Create)
# ---------------------------------------------------------------------
with st.expander("➕ Tambah Buku Manual"):
    with st.form("form_add_book", clear_on_submit=True):
        title = st.text_input("Judul Buku")
        price = st.text_input("Harga (mis. £51.77)")
        rating = st.selectbox("Rating", ["1", "2", "3", "4", "5"])
        availability = st.text_input("Status Stok", value="In stock")
        submitted = st.form_submit_button("Simpan")
        if submitted:
            if title:
                db.insert_book(title, price, rating, availability, source_url="manual")
                st.success("Buku berhasil ditambahkan.")
                st.rerun()
            else:
                st.warning("Judul buku wajib diisi.")

# ---------------------------------------------------------------------
# 3. Tampilan katalog gabungan (Read) — INTI dari penyatuan dua sumber data
# ---------------------------------------------------------------------
st.subheader("📋 Katalog Buku (Scraping + API digabung)")

catalog = db.get_catalog_view()

if not catalog:
    st.info("Belum ada data. Silakan scraping atau tambah buku manual dulu.")
else:
    df = pd.DataFrame(catalog)
    st.dataframe(df, use_container_width=True)

    # -------------------------------------------------------------
    # 4. Detail per buku: enrich via API, edit, delete
    # -------------------------------------------------------------
    st.subheader("🔍 Detail & Kelola Buku")

    books = db.get_all_books()
    selected_id = st.selectbox(
        "Pilih Buku",
        options=[b["id"] for b in books],
        format_func=lambda i: next(b["title"] for b in books if b["id"] == i),
    )

    book = db.get_book(selected_id)
    enrichment = db.get_enrichment_by_book(selected_id)

    left, right = st.columns(2)

    # --- Kolom kiri: data hasil scraping (Update / Delete) ---
    with left:
        st.markdown("#### 📦 Data Scraping")
        with st.form("form_edit_book"):
            new_title = st.text_input("Judul", value=book["title"])
            new_price = st.text_input("Harga", value=book["price"])
            new_rating = st.selectbox(
                "Rating", ["1", "2", "3", "4", "5"],
                index=["1", "2", "3", "4", "5"].index(book["rating"]) if book["rating"] in ["1","2","3","4","5"] else 0,
            )
            new_availability = st.text_input("Stok", value=book["availability"])

            c1, c2 = st.columns(2)
            with c1:
                update_btn = st.form_submit_button("💾 Update")
            with c2:
                delete_btn = st.form_submit_button("🗑️ Hapus Buku Ini")

            if update_btn:
                db.update_book(selected_id, new_title, new_price, new_rating, new_availability)
                st.success("Data buku berhasil diupdate.")
                st.rerun()

            if delete_btn:
                db.delete_book(selected_id)
                st.success("Buku (dan data pelengkapnya) berhasil dihapus.")
                st.rerun()

    # --- Kolom kanan: data hasil API (Enrich / Update / Delete) ---
    with right:
        st.markdown("#### 🌐 Data Pelengkap (API - Open Library)")

        if not enrichment:
            st.info("Buku ini belum punya data pelengkap.")
            if st.button("Ambil Detail dari API"):
                with st.spinner("Mencari data di Open Library..."):
                    result = api_client.enrich_book(selected_id)
                if result:
                    st.success("Data pelengkap berhasil diambil.")
                    st.rerun()
                else:
                    st.warning("Data tidak ditemukan di Open Library untuk judul ini.")
        else:
            with st.form("form_edit_enrichment"):
                new_author = st.text_input("Penulis", value=enrichment["author"] or "")
                new_year = st.text_input("Tahun Terbit Pertama", value=enrichment["first_publish_year"] or "")
                new_subjects = st.text_input("Subjek/Tema", value=enrichment["subjects"] or "")
                new_description = st.text_area("Deskripsi Singkat", value=enrichment["description"] or "")

                c1, c2 = st.columns(2)
                with c1:
                    update_enrich_btn = st.form_submit_button("💾 Update")
                with c2:
                    delete_enrich_btn = st.form_submit_button("🗑️ Hapus Data Pelengkap")

                if update_enrich_btn:
                    db.upsert_enrichment(selected_id, new_author, new_year, new_subjects, new_description)
                    st.success("Data pelengkap berhasil diupdate.")
                    st.rerun()

                if delete_enrich_btn:
                    db.delete_enrichment(selected_id)
                    st.success("Data pelengkap berhasil dihapus.")
                    st.rerun()

            if st.button("🔄 Tarik Ulang dari API"):
                with st.spinner("Mengambil ulang data dari Open Library..."):
                    result = api_client.enrich_book(selected_id)
                if result:
                    st.success("Data pelengkap berhasil diperbarui.")
                    st.rerun()
                else:
                    st.warning("Data tidak ditemukan di Open Library untuk judul ini.")
