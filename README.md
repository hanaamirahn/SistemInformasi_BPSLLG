# Sistem Informasi Katalog Buku (Scraping + API dalam Satu Studi Kasus)

Aplikasi Streamlit dengan **satu studi kasus terpadu**: Katalog Buku.
Bukan dua fitur yang berdiri sendiri, tapi dua sumber data yang saling melengkapi:

- **Web Scraping** (books.toscrape.com) -> data dasar buku: judul, harga, rating, stok
- **API** (Open Library) -> data pelengkap buku yang sama: penulis, tahun terbit, subjek, deskripsi

Kedua data ini digabung lewat relasi `book_id` dan ditampilkan sebagai **satu katalog**.

## Tech Stack
- **Bahasa**: Python 3
- **Framework**: Streamlit
- **Database**: SQLite
- **Scraping**: requests + BeautifulSoup4
- **API Client**: requests (Open Library Search API, gratis, tanpa API key)

## Struktur File
```
app.py          -> entry point Streamlit, satu halaman katalog terpadu
db.py           -> koneksi database & seluruh fungsi CRUD (2 tabel + join)
scraper.py      -> scraping books.toscrape.com -> tabel `books`
api_client.py   -> enrichment dari Open Library -> tabel `book_enrichment`
requirements.txt-> daftar dependency
```

## Rancangan Database (relasional, 1 entitas: Buku)
```
books                          book_enrichment
├── id (PK)                    ├── id (PK)
├── title                      ├── book_id (FK -> books.id)
├── price                      ├── author
├── rating                     ├── first_publish_year
├── availability               ├── subjects
├── source_url                 ├── description
└── scraped_at                 └── fetched_at
```
- 1 baris `books` <-> 0 atau 1 baris `book_enrichment`
- Hapus buku di `books` otomatis menghapus data pelengkapnya (cascade manual di `db.delete_book`)
- `db.get_catalog_view()` melakukan LEFT JOIN kedua tabel untuk ditampilkan sebagai satu katalog

## Alur Logika Program
1. User klik **"Scrape Buku Baru"** -> `scraper.py` mengambil data dari books.toscrape.com -> disimpan ke tabel `books`
2. User pilih salah satu buku di katalog -> klik **"Ambil Detail dari API"** -> `api_client.py` mencari judul yang sama di Open Library -> hasilnya disimpan ke `book_enrichment` dengan `book_id` yang sesuai
3. Tabel katalog di halaman utama menampilkan **gabungan** kedua tabel (join), sehingga terlihat sebagai satu data buku yang utuh
4. Semua field (baik dari scraping maupun API) bisa di-**Update** dan di-**Delete** langsung dari panel "Detail & Kelola Buku"

## Cara Menjalankan Lokal
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Cara Deploy ke Streamlit Community Cloud
1. Push semua file ini ke repository GitHub.
2. Buka https://share.streamlit.io/ -> login dengan GitHub.
3. New app -> pilih repo, branch `main`, file utama `app.py`.
4. Deploy.

## Catatan
- Filesystem Streamlit Community Cloud bersifat sementara — `data.db` bisa ter-reset
  saat redeploy. Untuk kebutuhan data permanen, bisa migrasi ke database eksternal
  (mis. Supabase/Postgres) tanpa mengubah struktur logika di atas.
- Pencarian di Open Library dilakukan berdasarkan judul buku; kadang hasil tidak
  100% cocok karena API mengembalikan kecocokan judul terdekat, bukan pencarian ISBN persis.
