"""
app.py
Sistem Informasi Buku — 2 Fitur CRUD Terpisah

Halaman:
🏠 Dashboard             -> ringkasan kedua fitur (jumlah data, grafik status)
📦 Data Web Scraping     -> FITUR 1: scrape + CRUD penuh
🔍 Cari Buku (API)       -> FITUR 2a: cari via Open Library API + tombol simpan
📖 Koleksi Saya          -> FITUR 2b: CRUD penuh atas buku yang disimpan
ℹ️ Tentang               -> penjelasan proyek & tech stack
"""

import streamlit as st
import pandas as pd
import plotly.express as px

import db
import scraper
import api_client

# =======================================================================
# KONFIGURASI HALAMAN & INISIALISASI DATABASE
# =======================================================================

st.set_page_config(
    page_title="Sistem Informasi Buku",
    page_icon="📚",
    layout="wide",
)

# Membuat tabel database jika belum ada (aman dipanggil berulang kali)
db.init_db()

# =======================================================================
# SIDEBAR NAVIGASI
# =======================================================================

st.sidebar.title("📚 Sistem Informasi Buku")

halaman = st.sidebar.radio(
    "Navigasi",
    [
        "🏠 Dashboard",
        "📦 Data Web Scraping",
        "🔍 Cari Buku (API)",
        "📖 Koleksi Saya",
        "ℹ️ Tentang",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption("Fitur 1: Web Scraping (books.toscrape.com)")
st.sidebar.caption("Fitur 2: API (Open Library)")


# =======================================================================
# HALAMAN: DASHBOARD
# =======================================================================

def halaman_dashboard():
    st.title("🏠 Dashboard")
    st.write("Ringkasan data dari kedua fitur.")

    stats = db.get_dashboard_stats()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Data Scraping", stats["total_scraped"])
    col2.metric("Total Koleksi Buku", stats["total_koleksi"])
    col3.metric("Rata-rata Rating Pribadi", stats["avg_rating"])

    st.markdown("---")

    if stats["status_breakdown"]:
        st.subheader("Status Bacaan Koleksi")

        df_status = pd.DataFrame(
            {
                "status": list(stats["status_breakdown"].keys()),
                "jumlah": list(stats["status_breakdown"].values()),
            }
        )

        fig = px.pie(
            df_status,
            names="status",
            values="jumlah",
            title="Distribusi Status Bacaan",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Belum ada data koleksi buku untuk ditampilkan grafiknya.")


# =======================================================================
# HALAMAN: DATA WEB SCRAPING (FITUR 1 - CRUD)
# =======================================================================

def halaman_scraping():
    st.title("📦 Data Web Scraping")
    st.write("Mengambil data buku dari books.toscrape.com dan mengelolanya (CRUD).")

    # --- CREATE: tombol scrape ---
    with st.form("form_scrape"):
        jumlah_halaman = st.number_input(
            "Jumlah halaman yang ingin di-scrape", min_value=1, max_value=10, value=1
        )
        submit_scrape = st.form_submit_button("Scrape Sekarang")

    if submit_scrape:
        with st.spinner("Mengambil data dari books.toscrape.com..."):
            total_saved = scraper.scrape_books(pages=jumlah_halaman)
        st.success(f"Berhasil menyimpan {total_saved} buku baru.")
        st.rerun()

    st.markdown("---")

    # --- READ ---
    data = db.get_all_scraped_books()

    if not data:
        st.info("Belum ada data. Klik 'Scrape Sekarang' untuk mengambil data.")
        return

    st.subheader(f"Data Tersimpan ({len(data)} buku)")
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.subheader("Edit / Hapus Data")

    pilihan_id = st.selectbox(
        "Pilih buku (berdasarkan ID)",
        options=[row["id"] for row in data],
        format_func=lambda i: f"#{i} - " + next(r["title"] for r in data if r["id"] == i),
    )

    buku = db.get_scraped_book(pilihan_id)

    with st.form("form_edit_scrape"):
        title = st.text_input("Judul", value=buku["title"])
        price = st.text_input("Harga", value=buku["price"])
        rating = st.selectbox(
            "Rating",
            options=["1", "2", "3", "4", "5"],
            index=max(0, int(buku["rating"]) - 1) if buku["rating"] else 0,
        )
        availability = st.text_input("Ketersediaan", value=buku["availability"])

        col_edit, col_hapus = st.columns(2)
        submit_edit = col_edit.form_submit_button("💾 Simpan Perubahan")
        submit_hapus = col_hapus.form_submit_button("🗑️ Hapus Buku")

    if submit_edit:
        db.update_scraped_book(pilihan_id, title, price, rating, availability)
        st.success("Data berhasil diperbarui.")
        st.rerun()

    if submit_hapus:
        db.delete_scraped_book(pilihan_id)
        st.success("Data berhasil dihapus.")
        st.rerun()


# =======================================================================
# HALAMAN: CARI BUKU (FITUR 2a - API)
# =======================================================================

def halaman_cari_api():
    st.title("🔍 Cari Buku (Open Library API)")
    st.write("Cari buku berdasarkan judul, lalu simpan ke Koleksi Saya.")

    query = st.text_input("Kata kunci pencarian", placeholder="Contoh: Harry Potter")
    max_results = st.slider("Jumlah hasil maksimal", 1, 20, 10)
    cari = st.button("Cari Buku")

    if not cari:
        return

    with st.spinner("Mencari buku..."):
        results, debug_info = api_client.search_books_api(query, max_results)

    if debug_info.get("error"):
        st.warning(debug_info["error"])

    if not results:
        return

    st.success(f"Ditemukan {len(results)} buku (dari total {debug_info.get('total_ditemukan_api', 0)} di API).")

    for buku in results:
        with st.container(border=True):
            col_img, col_info = st.columns([1, 4])

            with col_img:
                if buku["cover_url"]:
                    st.image(buku["cover_url"], width=100)
                else:
                    st.write("Tidak ada cover")

            with col_info:
                st.markdown(f"**{buku['title']}**")
                st.caption(f"Penulis: {buku['authors']} · Tahun: {buku['published_year']} · ISBN: {buku['isbn']}")
                st.write(buku["description"])

                sudah_tersimpan = db.is_already_saved(buku["isbn"], buku["title"])

                if sudah_tersimpan:
                    st.caption("✅ Sudah ada di koleksi")
                else:
                    if st.button("➕ Simpan ke Koleksi", key=f"simpan_{buku['isbn']}_{buku['title']}"):
                        db.insert_koleksi(
                            buku["title"],
                            buku["authors"],
                            buku["published_year"],
                            buku["isbn"],
                            buku["cover_url"],
                            buku["description"],
                        )
                        st.success("Buku disimpan ke koleksi.")
                        st.rerun()


# =======================================================================
# HALAMAN: KOLEKSI SAYA (FITUR 2b - CRUD)
# =======================================================================

def halaman_koleksi():
    st.title("📖 Koleksi Saya")
    st.write("Kelola buku yang sudah kamu simpan dari hasil pencarian API.")

    data = db.get_all_koleksi()

    if not data:
        st.info("Koleksi masih kosong. Cari buku dulu di halaman 'Cari Buku (API)'.")
        return

    st.subheader(f"Total Koleksi: {len(data)} buku")

    for buku in data:
        with st.expander(f"{buku['title']} — {buku['authors']}"):
            col_img, col_info = st.columns([1, 4])

            with col_img:
                if buku["cover_url"]:
                    st.image(buku["cover_url"], width=100)

            with col_info:
                st.caption(f"Tahun: {buku['published_year']} · ISBN: {buku['isbn']}")
                st.write(buku["description"])

            with st.form(f"form_koleksi_{buku['id']}"):
                status_baca = st.selectbox(
                    "Status Baca",
                    options=["Belum Dibaca", "Sedang Dibaca", "Selesai Dibaca"],
                    index=["Belum Dibaca", "Sedang Dibaca", "Selesai Dibaca"].index(buku["status_baca"])
                    if buku["status_baca"] in ["Belum Dibaca", "Sedang Dibaca", "Selesai Dibaca"]
                    else 0,
                )
                rating_pribadi = st.slider(
                    "Rating Pribadi", 0, 5, value=buku["rating_pribadi"] or 0
                )
                catatan_pribadi = st.text_area(
                    "Catatan Pribadi", value=buku["catatan_pribadi"] or ""
                )

                col_simpan, col_hapus = st.columns(2)
                simpan = col_simpan.form_submit_button("💾 Simpan Perubahan")
                hapus = col_hapus.form_submit_button("🗑️ Hapus dari Koleksi")

            if simpan:
                db.update_koleksi(buku["id"], status_baca, rating_pribadi, catatan_pribadi)
                st.success("Perubahan disimpan.")
                st.rerun()

            if hapus:
                db.delete_koleksi(buku["id"])
                st.success("Buku dihapus dari koleksi.")
                st.rerun()


# =======================================================================
# HALAMAN: TENTANG
# =======================================================================

def halaman_tentang():
    st.title("ℹ️ Tentang")
    st.markdown(
        """
        **Sistem Informasi Buku** adalah aplikasi Streamlit dengan dua sistem
        CRUD yang berdiri sendiri-sendiri:

        1. **Fitur 1 — Web Scraping**: mengambil data buku dari
           [books.toscrape.com](https://books.toscrape.com) menggunakan
           `requests` + `BeautifulSoup4`, disimpan di tabel `scraped_books`.
        2. **Fitur 2 — API**: mencari buku lewat
           [Open Library API](https://openlibrary.org/developers/api),
           disimpan sebagai koleksi pribadi di tabel `koleksi_buku`.

        **Tech Stack**
        - Bahasa: Python 3
        - Framework: Streamlit
        - Database: SQLite (2 tabel independen)
        - Scraping: requests + BeautifulSoup4
        - API: Open Library API (gratis, tanpa API key)

        Filesystem Streamlit Community Cloud bersifat sementara — `data.db`
        bisa ter-reset saat redeploy/reboot.
        """
    )


# =======================================================================
# ROUTER HALAMAN
# =======================================================================

if halaman == "🏠 Dashboard":
    halaman_dashboard()
elif halaman == "📦 Data Web Scraping":
    halaman_scraping()
elif halaman == "🔍 Cari Buku (API)":
    halaman_cari_api()
elif halaman == "📖 Koleksi Saya":
    halaman_koleksi()
elif halaman == "ℹ️ Tentang":
    halaman_tentang()
