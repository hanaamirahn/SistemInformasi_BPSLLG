"""
app.py
Aplikasi utama Streamlit.

Studi kasus: Sistem Informasi Katalog Buku
Dibuat sebagai WIZARD 3 LANGKAH supaya pengguna awam tidak bingung:
  Langkah 1: Ambil Buku Baru        (web scraping)
  Langkah 2: Lengkapi Informasi Buku (tarik data API)
  Langkah 3: Kelola Semua Buku       (edit / hapus - CRUD penuh)
"""

import streamlit as st
import pandas as pd

import db
import scraper
import api_client

st.set_page_config(page_title="Katalog Buku", layout="wide")

db.init_db()

# ---------------------------------------------------------------------
# Sidebar: navigasi wizard
# ---------------------------------------------------------------------
st.sidebar.title("📚 Katalog Buku")
st.sidebar.caption("Ikuti langkah 1 → 2 → 3 secara berurutan kalau ini pertama kali Anda pakai.")

langkah = st.sidebar.radio(
    "Langkah:",
    ["1️⃣ Ambil Buku Baru", "2️⃣ Lengkapi Informasi Buku", "3️⃣ Kelola Semua Buku"],
)

semua_buku = db.get_all_books_with_status()
total_buku = len(semua_buku)
sudah_lengkap = sum(1 for b in semua_buku if b["sudah_lengkap"])

st.sidebar.markdown("---")
st.sidebar.metric("Total Buku", total_buku)
st.sidebar.metric("Sudah Lengkap", f"{sudah_lengkap}/{total_buku}" if total_buku else "0/0")


# =======================================================================
# LANGKAH 1: Ambil Buku Baru (Scraping)
# =======================================================================
if langkah == "1️⃣ Ambil Buku Baru":
    st.title("Langkah 1: Ambil Buku Baru")
    st.write(
        "Klik tombol di bawah untuk mengambil daftar buku secara otomatis dari internet. "
        "Sistem akan menyimpannya sendiri — Anda tidak perlu mengetik apa pun."
    )

    jumlah_halaman = st.slider("Berapa banyak data yang ingin diambil?", min_value=1, max_value=10, value=1)
    st.caption(f"Perkiraan: sekitar {jumlah_halaman * 20} buku akan ditambahkan.")

    if st.button("📥 Ambil Buku Sekarang", type="primary"):
        with st.spinner("Sedang mengambil data buku, mohon tunggu..."):
            jumlah = scraper.scrape_books(pages=jumlah_halaman)
        if jumlah > 0:
            st.success(f"Berhasil! {jumlah} buku baru sudah ditambahkan ke katalog Anda.")
            st.info("Sekarang buka **Langkah 2** di menu sebelah kiri untuk melengkapi info buku.")
        else:
            st.warning("Tidak ada data baru yang berhasil diambil. Coba lagi beberapa saat lagi.")

    st.markdown("---")
    with st.expander("✍️ Atau, tambahkan buku sendiri secara manual"):
        with st.form("form_tambah_manual", clear_on_submit=True):
            judul = st.text_input("Judul Buku")
            harga = st.text_input("Harga (contoh: £51.77)")
            rating = st.select_slider("Rating (bintang)", options=["1", "2", "3", "4", "5"], value="5")
            stok = st.text_input("Status Stok", value="In stock")
            simpan = st.form_submit_button("Simpan Buku Ini")
            if simpan:
                if judul:
                    db.insert_book(judul, harga, rating, stok, source_url="manual")
                    st.success("Buku berhasil ditambahkan secara manual.")
                    st.rerun()
                else:
                    st.warning("Judul buku wajib diisi.")

    if total_buku > 0:
        st.markdown("---")
        st.caption(f"Anda sudah punya {total_buku} buku di katalog:")
        st.dataframe(
            pd.DataFrame(semua_buku)[["title", "price", "rating", "availability"]]
              .rename(columns={"title": "Judul", "price": "Harga", "rating": "Rating", "availability": "Stok"}),
            use_container_width=True,
            hide_index=True,
        )


# =======================================================================
# LANGKAH 2: Lengkapi Informasi Buku (API)
# =======================================================================
elif langkah == "2️⃣ Lengkapi Informasi Buku":
    st.title("Langkah 2: Lengkapi Informasi Buku")
    st.write(
        "Pilih salah satu buku, lalu klik tombol untuk mencari **penulis, tahun terbit, dan deskripsi** "
        "buku itu secara otomatis dari internet."
    )

    if total_buku == 0:
        st.warning("Anda belum punya buku sama sekali. Buka **Langkah 1** dulu untuk mengambil data buku.")
    else:
        pilihan = st.selectbox(
            "Pilih buku:",
            options=semua_buku,
            format_func=lambda b: f"{'✅' if b['sudah_lengkap'] else '⭕'}  {b['title']}",
        )

        st.markdown("---")
        col_kiri, col_kanan = st.columns(2)

        with col_kiri:
            st.markdown("#### 📖 Info Dasar")
            st.write(f"**Judul:** {pilihan['title']}")
            st.write(f"**Harga:** {pilihan['price']}")
            st.write(f"**Rating:** {'⭐' * int(pilihan['rating']) if str(pilihan['rating']).isdigit() else pilihan['rating']}")
            st.write(f"**Stok:** {pilihan['availability']}")

        with col_kanan:
            st.markdown("#### 🔎 Info Tambahan")
            enrichment = db.get_enrichment_by_book(pilihan["id"])

            if not enrichment:
                st.info("Buku ini belum punya info tambahan.")
                if st.button("🔍 Cari Info Tambahan Sekarang", type="primary"):
                    with st.spinner("Mencari informasi buku ini di internet..."):
                        hasil = api_client.enrich_book(pilihan["id"])
                    if hasil:
                        st.success("Berhasil! Info tambahan sudah ditemukan.")
                        st.rerun()
                    else:
                        st.warning("Maaf, informasi untuk buku ini tidak ditemukan. Coba buku lain.")
            else:
                st.write(f"**Penulis:** {enrichment['author']}")
                st.write(f"**Tahun Terbit Pertama:** {enrichment['first_publish_year']}")
                st.write(f"**Tema/Subjek:** {enrichment['subjects']}")
                st.write(f"**Deskripsi:** {enrichment['description']}")
                if st.button("🔄 Cari Ulang Info Ini"):
                    with st.spinner("Mencari ulang informasi..."):
                        hasil = api_client.enrich_book(pilihan["id"])
                    if hasil:
                        st.success("Info tambahan berhasil diperbarui.")
                        st.rerun()
                    else:
                        st.warning("Informasi tidak ditemukan.")

        st.markdown("---")
        st.caption(f"Progres: {sudah_lengkap} dari {total_buku} buku sudah lengkap.")
        st.progress(sudah_lengkap / total_buku if total_buku else 0)
        if sudah_lengkap == total_buku:
            st.success("Semua buku sudah lengkap! Buka **Langkah 3** untuk melihat atau mengelola semuanya.")


# =======================================================================
# LANGKAH 3: Kelola Semua Buku (CRUD penuh)
# =======================================================================
elif langkah == "3️⃣ Kelola Semua Buku":
    st.title("Langkah 3: Kelola Semua Buku")
    st.write("Di sini Anda bisa melihat semua data buku, mengubah isinya, atau menghapus buku yang tidak diperlukan.")

    if total_buku == 0:
        st.warning("Anda belum punya buku sama sekali. Buka **Langkah 1** dulu untuk mengambil data buku.")
    else:
        katalog = db.get_catalog_view()
        st.dataframe(pd.DataFrame(katalog), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("✏️ Ubah atau Hapus Satu Buku")

        buku_terpilih = st.selectbox(
            "Pilih buku yang ingin diubah/dihapus:",
            options=semua_buku,
            format_func=lambda b: b["title"],
            key="pilih_buku_kelola",
        )
        enrichment = db.get_enrichment_by_book(buku_terpilih["id"])

        with st.form("form_kelola_buku"):
            st.markdown("**Info Dasar**")
            judul = st.text_input("Judul", value=buku_terpilih["title"])
            harga = st.text_input("Harga", value=buku_terpilih["price"])
            rating = st.select_slider(
                "Rating", options=["1", "2", "3", "4", "5"],
                value=buku_terpilih["rating"] if buku_terpilih["rating"] in ["1", "2", "3", "4", "5"] else "5",
            )
            stok = st.text_input("Stok", value=buku_terpilih["availability"])

            st.markdown("**Info Tambahan** (kosongkan kalau belum ada)")
            penulis = st.text_input("Penulis", value=enrichment["author"] if enrichment else "")
            tahun = st.text_input("Tahun Terbit", value=enrichment["first_publish_year"] if enrichment else "")
            deskripsi = st.text_area("Deskripsi", value=enrichment["description"] if enrichment else "")

            c1, c2 = st.columns(2)
            with c1:
                simpan_btn = st.form_submit_button("💾 Simpan Perubahan", type="primary")
            with c2:
                hapus_btn = st.form_submit_button("🗑️ Hapus Buku Ini")

            if simpan_btn:
                db.update_book(buku_terpilih["id"], judul, harga, rating, stok)
                if penulis or tahun or deskripsi:
                    db.upsert_enrichment(
                        buku_terpilih["id"], penulis, tahun,
                        enrichment["subjects"] if enrichment else "-", deskripsi,
                    )
                st.success("Perubahan berhasil disimpan.")
                st.rerun()

            if hapus_btn:
                db.delete_book(buku_terpilih["id"])
                st.success(f"Buku '{buku_terpilih['title']}' berhasil dihapus.")
                st.rerun()
