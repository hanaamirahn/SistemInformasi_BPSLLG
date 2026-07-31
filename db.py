"""
db.py
Modul untuk mengelola koneksi dan operasi CRUD ke database SQLite.

Studi kasus tunggal: KATALOG BUKU
Ada 2 tabel yang SALING TERHUBUNG (bukan dua dunia terpisah):
  1. books            -> data dasar buku hasil WEB SCRAPING (books.toscrape.com)
  2. book_enrichment  -> data pelengkap buku hasil TARIK API (Open Library),
                         terhubung ke `books` lewat kolom book_id (foreign key)

Satu baris di `books` bisa punya satu baris pelengkap di `book_enrichment`.
Keduanya menggambarkan entitas yang sama: SATU BUKU.
"""

import sqlite3
from datetime import datetime

DB_NAME = "data.db"


def get_connection():
    """Buka koneksi ke database SQLite."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Buat tabel jika belum ada. Dipanggil sekali saat app start."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price TEXT,
            rating TEXT,
            availability TEXT,
            source_url TEXT,
            scraped_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS book_enrichment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            author TEXT,
            first_publish_year TEXT,
            subjects TEXT,
            description TEXT,
            fetched_at TEXT,
            FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------
# CRUD: books (hasil scraping)
# ---------------------------------------------------------------------

def insert_book(title, price, rating, availability, source_url=""):
    conn = get_connection()
    conn.execute(
        """INSERT INTO books (title, price, rating, availability, source_url, scraped_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (title, price, rating, availability, source_url,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()


def get_all_books():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM books ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_book(book_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_book(book_id, title, price, rating, availability):
    conn = get_connection()
    conn.execute(
        "UPDATE books SET title=?, price=?, rating=?, availability=? WHERE id=?",
        (title, price, rating, availability, book_id),
    )
    conn.commit()
    conn.close()


def delete_book(book_id):
    """Hapus buku sekaligus data pelengkapnya (cascade manual, aman untuk semua versi SQLite)."""
    conn = get_connection()
    conn.execute("DELETE FROM book_enrichment WHERE book_id=?", (book_id,))
    conn.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------
# CRUD: book_enrichment (hasil tarik API)
# ---------------------------------------------------------------------

def get_enrichment_by_book(book_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM book_enrichment WHERE book_id=?", (book_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def upsert_enrichment(book_id, author, first_publish_year, subjects, description):
    """Simpan data pelengkap. Kalau sudah ada untuk book_id ini, di-update; kalau belum, dibuat baru."""
    existing = get_enrichment_by_book(book_id)
    conn = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if existing:
        conn.execute(
            """UPDATE book_enrichment
               SET author=?, first_publish_year=?, subjects=?, description=?, fetched_at=?
               WHERE book_id=?""",
            (author, first_publish_year, subjects, description, now, book_id),
        )
    else:
        conn.execute(
            """INSERT INTO book_enrichment
               (book_id, author, first_publish_year, subjects, description, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (book_id, author, first_publish_year, subjects, description, now),
        )
    conn.commit()
    conn.close()


def delete_enrichment(book_id):
    conn = get_connection()
    conn.execute("DELETE FROM book_enrichment WHERE book_id=?", (book_id,))
    conn.commit()
    conn.close()


def get_all_books_with_status():
    """
    Sama seperti get_all_books, tapi tiap buku ditandai status kelengkapannya:
    sudah_lengkap = 1 kalau buku ini sudah punya data pelengkap dari API, 0 kalau belum.
    Dipakai supaya tampilan wizard bisa menunjukkan mana buku yang perlu dilengkapi.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT b.*,
               CASE WHEN e.id IS NOT NULL THEN 1 ELSE 0 END AS sudah_lengkap
        FROM books b
        LEFT JOIN book_enrichment e ON b.id = e.book_id
        ORDER BY b.id DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_catalog_view():
    """
    Gabungan (LEFT JOIN) books + book_enrichment.
    Ini yang jadi 'satu studi kasus' -> satu tampilan katalog buku lengkap,
    walau datanya berasal dari 2 sumber (scraping & API) dan 2 tabel berbeda.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT b.id, b.title, b.price, b.rating, b.availability, b.scraped_at,
               e.author, e.first_publish_year, e.subjects, e.description, e.fetched_at
        FROM books b
        LEFT JOIN book_enrichment e ON b.id = e.book_id
        ORDER BY b.id DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
