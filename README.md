# Sistem Informasi Buku — 2 Fitur CRUD Terpisah

Aplikasi Streamlit dengan **2 sistem CRUD yang benar-benar independen**, sesuai
syarat tugas, dibungkus dalam 1 website dengan navigasi yang jelas:

1. **Fitur 1 — CRUD Data Web Scraping**: mengambil data buku otomatis dari
   [books.toscrape.com](https://books.toscrape.com), dikelola penuh (Create,
   Read, Update, Delete) di halaman **📦 Data Web Scraping**.
2. **Fitur 2 — CRUD Data API**: mencari buku lewat **Google Books API**,
   menyimpannya sebagai koleksi pribadi (dengan status baca, rating, catatan),
   dikelola penuh di halaman **📖 Koleksi Saya**.

## Struktur Halaman
```
🏠 Dashboard             -> ringkasan kedua fitur (jumlah data, grafik status)
📦 Data Web Scraping     -> FITUR 1: scrape + CRUD penuh
🔍 Cari Buku (API)       -> FITUR 2a: cari via Google Books API + tombol simpan
📖 Koleksi Saya          -> FITUR 2b: CRUD penuh atas buku yang disimpan
ℹ️ Tentang               -> penjelasan proyek & tech stack
```

## Tech Stack
- **Bahasa**: Python 3
- **Framework**: Streamlit
- **Database**: SQLite (2 tabel independen: `scraped_books`, `koleksi_buku`)
- **Scraping**: requests + BeautifulSoup4
- **API**: Google Books API (gratis, tanpa API key)

## Struktur File
```
app.py          -> semua UI, 5 halaman via sidebar
db.py           -> koneksi database & CRUD kedua fitur + statistik dashboard
scraper.py      -> Fitur 1: scraping books.toscrape.com
api_client.py   -> Fitur 2: pencarian Google Books API
requirements.txt-> daftar dependency
```

## Rancangan Database
```
scraped_books (Fitur 1)        koleksi_buku (Fitur 2)
├── id (PK)                    ├── id (PK)
├── title                      ├── title
├── price                      ├── authors
├── rating                     ├── published_year
├── availability                ├── isbn
├── source_url                 ├── cover_url
└── scraped_at                 ├── description
                                ├── status_baca
                                ├── rating_pribadi
                                ├── catatan_pribadi
                                └── added_at
```
Kedua tabel ini **independen** — tidak ada foreign key di antara keduanya,
karena masing-masing memang harus berdiri sebagai sistem CRUD tersendiri.

## Alur Logika Program

**Fitur 1 (Scraping):**
1. User klik "Scrape Sekarang" -> `scraper.py` ambil HTML dari books.toscrape.com
2. Data diparsing (judul, harga, rating, stok) -> disimpan ke `scraped_books`
3. User bisa edit/hapus langsung dari tabel di halaman yang sama

**Fitur 2 (API):**
1. User ketik judul di kolom pencarian -> `api_client.py` request ke Google Books API
2. Hasil pencarian (belum disimpan) ditampilkan sebagai kartu dengan tombol "Simpan ke Koleksi"
3. Saat disimpan -> masuk ke `koleksi_buku`
4. Di halaman "Koleksi Saya", user bisa ubah status baca/rating/catatan, atau hapus buku

## Cara Menjalankan Lokal
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Cara Deploy ke Streamlit Community Cloud
1. Push semua file ke GitHub (ganti semua file lama termasuk `db.py`, `api_client.py`).
2. share.streamlit.io -> New app -> pilih repo, branch `main`, file utama `app.py`.
3. Deploy, tunggu, lalu buka link yang diberikan.

## Catatan Penting
- Filesystem Streamlit Community Cloud bersifat sementara — `data.db` bisa
  ter-reset saat redeploy/reboot. Untuk data permanen, backup manual atau
  migrasi ke database eksternal (Supabase/Postgres).
- Google Books API punya kuota harian untuk request tanpa API key — cukup
  untuk penggunaan wajar/demo, tapi kalau kena limit, coba lagi nanti.
