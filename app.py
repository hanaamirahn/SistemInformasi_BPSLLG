"""
app.py
Sistem Informasi Buku — 2 fitur CRUD yang terpisah, dibungkus 1 website.

Halaman:
  🏠 Dashboard             -> ringkasan kedua fitur
  📦 Data Web Scraping     -> FITUR 1: CRUD penuh data hasil scraping
  🔍 Cari Buku (API)       -> FITUR 2a: cari buku lewat Google Books API
  📖 Koleksi Saya          -> FITUR 2b: CRUD penuh atas buku yang disimpan dari API
  ℹ️ Tentang               -> penjelasan proyek
"""

import streamlit as st
import pandas as pd

import db
import scraper
import api_client

st.set_page_config(page_title="Sistem Informasi Buku", layout="wide")
db.init_db()

# ---------------------------------------------------------------------
# Sidebar navigasi
# ---------------------------------------------------------------------
st.sidebar.title("📚 Sistem Informasi Buku")
halaman = st.sidebar.radio(
    "Navigasi",
    ["🏠 Dashboard", "📦 Data Web Scraping", "🔍 Cari Buku (API)", "📖 Koleksi Saya", "ℹ️ Tentang"],
)

stats = db.get_dashboard_stats()
st.sidebar.markdown("---")
st.sidebar.caption("Ringkasan Cepat")
st.sidebar.write(f"📦 Data Scraping: **{stats['total_scraped']}**")
st.sidebar.write(f"📖 Koleksi API: **{stats['total_koleksi']}**")


# =======================================================================
# 🏠 DASHBOARD
# =======================================================================
if halaman == "🏠 Dashboard":
    st.title("🏠 Dashboard")
    st.write("Ringkasan dari kedua fitur sistem informasi ini.")

    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Total Data Scraping", stats["total_scraped"])
    col2.metric("📖 Total Koleksi (API)", stats["total_koleksi"])
    col3.metric("⭐ Rata-rata Rating Koleksi", stats["avg_rating"] if stats["avg_rating"] else "-")

    st.markdown("---")
    st.subheader("Status Bacaan Koleksi Saya")
    if stats["status_breakdown"]:
        df_status = pd.DataFrame(
            list(stats["status_breakdown"].items()), columns=["Status", "Jumlah"]
        )
        st.bar_chart(df_status.set_index("Status"))
    else:
        st.info("Belum ada buku di Koleksi Saya. Coba cari & simpan buku di menu **Cari Buku (API)**.")

    st.markdown("---")
    st.info(
        "**Cara pakai website ini:**\n\n"
        "1. Buka **📦 Data Web Scraping** untuk mengambil data buku otomatis dari internet (Fitur 1).\n"
        "2. Buka **🔍 Cari Buku (API)** untuk mencari buku tertentu dan menyimpannya ke koleksi pribadi (Fitur 2).\n"
        "3. Kelola datanya di **📦 Data Web Scraping** atau **📖 Koleksi Saya** — bisa diubah atau dihapus kapan saja."
    )


# =======================================================================
# 📦 FITUR 1: Data Web Scraping (CRUD)
# =======================================================================
elif halaman == "📦 Data Web Scraping":
    st.title("📦 Data Web Scraping")
    st.caption("Fitur 1: Sistem CRUD untuk data hasil Web Scraping (sumber: books.toscrape.com)")

    with st.expander("🔄 Ambil Data Baru dari Internet", expanded=(stats["total_scraped"] == 0)):
        st.write("Klik tombol di bawah untuk mengambil data buku secara otomatis.")
        jumlah_halaman = st.slider("Jumlah halaman yang diambil", 1, 10, 1)
        if st.button("📥 Scrape Sekarang", type="primary"):
            with st.spinner("Mengambil data dari books.toscrape.com..."):
                jumlah = scraper.scrape_books(pages=jumlah_halaman)
            if jumlah > 0:
                st.success(f"{jumlah} data buku baru berhasil disimpan.")
                st.rerun()
            else:
                st.warning("Tidak ada data baru yang berhasil diambil.")

    with st.expander("➕ Tambah Data Manual"):
        with st.form("form_tambah_scraping", clear_on_submit=True):
            judul = st.text_input("Judul Buku")
            harga = st.text_input("Harga (contoh: £51.77)")
            rating = st.select_slider("Rating", ["1", "2", "3", "4", "5"], value="5")
            stok = st.text_input("Status Stok", value="In stock")
            simpan = st.form_submit_button("Simpan")
            if simpan:
                if judul:
                    db.insert_scraped_book(judul, harga, rating, stok, source_url="manual")
                    st.success("Data berhasil ditambahkan.")
                    st.rerun()
                else:
                    st.warning("Judul wajib diisi.")

    st.markdown("---")
    st.subheader("📋 Semua Data Hasil Scraping")
    scraped = db.get_all_scraped_books()

    if not scraped:
        st.info("Belum ada data. Silakan scraping atau tambah data manual di atas.")
    else:
        st.dataframe(pd.DataFrame(scraped), use_container_width=True, hide_index=True)

        st.subheader("✏️ Edit / Hapus Data")
        pilihan = st.selectbox(
            "Pilih data:", options=scraped, format_func=lambda b: b["title"], key="pilih_scraping",
        )

        with st.form("form_edit_scraping"):
            new_judul = st.text_input("Judul", value=pilihan["title"])
            new_harga = st.text_input("Harga", value=pilihan["price"])
            new_rating = st.select_slider(
                "Rating", ["1", "2", "3", "4", "5"],
                value=pilihan["rating"] if pilihan["rating"] in ["1", "2", "3", "4", "5"] else "5",
            )
            new_stok = st.text_input("Stok", value=pilihan["availability"])

            c1, c2 = st.columns(2)
            with c1:
                update_btn = st.form_submit_button("💾 Update", type="primary")
            with c2:
                delete_btn = st.form_submit_button("🗑️ Hapus")

            if update_btn:
                db.update_scraped_book(pilihan["id"], new_judul, new_harga, new_rating, new_stok)
                st.success("Data berhasil diupdate.")
                st.rerun()

            if delete_btn:
                db.delete_scraped_book(pilihan["id"])
                st.success("Data berhasil dihapus.")
                st.rerun()


# =======================================================================
# 🔍 FITUR 2a: Cari Buku (API)
# =======================================================================
elif halaman == "🔍 Cari Buku (API)":
    st.title("🔍 Cari Buku (API)")
    st.caption("Fitur 2: Tarik data dari Google Books API, lalu simpan ke Koleksi Saya.")

    query = st.text_input("Ketik judul buku yang ingin dicari", placeholder="contoh: Atomic Habits")
    cari_btn = st.button("🔍 Cari", type="primary")

    if cari_btn and query:
        with st.spinner("Mencari buku..."):
            hasil = api_client.search_books_api(query)
        st.session_state["hasil_pencarian"] = hasil
        if not hasil:
            st.warning("Buku tidak ditemukan. Coba kata kunci lain.")

    hasil = st.session_state.get("hasil_pencarian", [])

    if hasil:
        st.markdown("---")
        st.subheader(f"Hasil Pencarian ({len(hasil)} buku)")

        for i, buku in enumerate(hasil):
            col_img, col_info = st.columns([1, 4])
            with col_img:
                if buku["cover_url"]:
                    st.image(buku["cover_url"], width=100)
                else:
                    st.write("📕")

            with col_info:
                st.markdown(f"**{buku['title']}**")
                st.caption(f"Penulis: {buku['authors']} · Tahun: {buku['published_year']} · ISBN: {buku['isbn']}")
                with st.expander("Lihat deskripsi"):
                    st.write(buku["description"])

                sudah_ada = db.is_already_saved(buku["isbn"], buku["title"])
                if sudah_ada:
                    st.caption("✅ Sudah ada di Koleksi Saya")
                else:
                    if st.button("💾 Simpan ke Koleksi", key=f"simpan_{i}"):
                        db.insert_koleksi(
                            buku["title"], buku["authors"], buku["published_year"],
                            buku["isbn"], buku["cover_url"], buku["description"],
                        )
                        st.success(f"'{buku['title']}' berhasil disimpan ke Koleksi Saya.")
                        st.rerun()
            st.markdown("---")


# =======================================================================
# 📖 FITUR 2b: Koleksi Saya (CRUD)
# =======================================================================
elif halaman == "📖 Koleksi Saya":
    st.title("📖 Koleksi Saya")
    st.caption("Fitur 2: Sistem CRUD untuk data yang disimpan dari hasil pencarian API.")

    koleksi = db.get_all_koleksi()

    if not koleksi:
        st.info("Koleksi Anda masih kosong. Buka **🔍 Cari Buku (API)** untuk menambah buku.")
    else:
        st.subheader("📋 Semua Buku di Koleksi")
        df = pd.DataFrame(koleksi)[["title", "authors", "published_year", "status_baca", "rating_pribadi"]]
        df.columns = ["Judul", "Penulis", "Tahun", "Status", "Rating"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("✏️ Edit / Hapus Buku")

        pilihan = st.selectbox(
            "Pilih buku:", options=koleksi, format_func=lambda b: b["title"], key="pilih_koleksi",
        )

        col_img, col_form = st.columns([1, 3])
        with col_img:
            if pilihan["cover_url"]:
                st.image(pilihan["cover_url"], width=140)
            st.caption(f"Penulis: {pilihan['authors']}")
            st.caption(f"Tahun: {pilihan['published_year']}")
            st.caption(f"ISBN: {pilihan['isbn']}")

        with col_form:
            with st.form("form_edit_koleksi"):
                status = st.selectbox(
                    "Status Bacaan",
                    ["Belum Dibaca", "Sedang Dibaca", "Selesai Dibaca"],
                    index=["Belum Dibaca", "Sedang Dibaca", "Selesai Dibaca"].index(pilihan["status_baca"])
                    if pilihan["status_baca"] in ["Belum Dibaca", "Sedang Dibaca", "Selesai Dibaca"] else 0,
                )
                rating = st.slider("Rating Pribadi", 0, 5, int(pilihan["rating_pribadi"] or 0))
                catatan = st.text_area("Catatan Pribadi", value=pilihan["catatan_pribadi"] or "")

                c1, c2 = st.columns(2)
                with c1:
                    update_btn = st.form_submit_button("💾 Simpan Perubahan", type="primary")
                with c2:
                    delete_btn = st.form_submit_button("🗑️ Hapus dari Koleksi")

                if update_btn:
                    db.update_koleksi(pilihan["id"], status, rating, catatan)
                    st.success("Perubahan berhasil disimpan.")
                    st.rerun()

                if delete_btn:
                    db.delete_koleksi(pilihan["id"])
                    st.success(f"'{pilihan['title']}' dihapus dari koleksi.")
                    st.rerun()


# =======================================================================
# ℹ️ TENTANG
# =======================================================================
elif halaman == "ℹ️ Tentang":
    st.title("ℹ️ Tentang Proyek Ini")
    st.markdown("""
    **Sistem Informasi Buku** ini dibuat untuk memenuhi 2 fitur utama:

    1. **Sistem CRUD data hasil Web Scraping** — mengambil data buku otomatis
       dari [books.toscrape.com](https://books.toscrape.com), lalu bisa ditambah,
       diubah, dan dihapus di halaman **📦 Data Web Scraping**.
    2. **Sistem CRUD data hasil tarik API** — mencari buku lewat
       [Google Books API](https://developers.google.com/books), menyimpannya
       sebagai koleksi pribadi, lalu bisa dikelola (status baca, rating, catatan)
       di halaman **📖 Koleksi Saya**.

    ### Teknologi yang Digunakan
    - **Bahasa**: Python 3
    - **Framework**: Streamlit
    - **Database**: SQLite
    - **Web Scraping**: requests + BeautifulSoup4
    - **API**: Google Books API (gratis, tanpa API key)
    - **Hosting**: Streamlit Community Cloud
    """)
