"""
db.py
Mengelola koneksi database SQLite dan seluruh operasi CRUD.

Terdapat dua sistem CRUD yang terpisah:
1. scraped_books  -> Menyimpan data hasil Web Scraping.
2. koleksi_buku   -> Menyimpan data hasil pencarian API.
"""

import sqlite3
from datetime import datetime

# Nama file database SQLite
DB_NAME = "data.db"


def get_connection():
    # Membuat koneksi ke database SQLite
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)

    # Mengubah hasil query menjadi dictionary (sqlite3.Row)
    conn.row_factory = sqlite3.Row

    return conn


def init_db():
    # Membuat tabel jika belum tersedia
    conn = get_connection()
    cur = conn.cursor()

    # Tabel untuk menyimpan data hasil web scraping
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scraped_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price TEXT,
            rating TEXT,
            availability TEXT,
            source_url TEXT,
            scraped_at TEXT
        )
    """)

    # Tabel untuk menyimpan koleksi buku hasil API
    cur.execute("""
        CREATE TABLE IF NOT EXISTS koleksi_buku (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            authors TEXT,
            published_year TEXT,
            isbn TEXT,
            cover_url TEXT,
            description TEXT,
            status_baca TEXT DEFAULT 'Belum Dibaca',
            rating_pribadi INTEGER DEFAULT 0,
            catatan_pribadi TEXT,
            added_at TEXT
        )
    """)

    # Menyimpan perubahan dan menutup koneksi
    conn.commit()
    conn.close()


# =======================================================================
# FITUR 1: CRUD tabel scraped_books (hasil Web Scraping)
# =======================================================================

def insert_scraped_book(title, price, rating, availability, source_url=""):
    # Menambahkan data buku hasil scraping ke database
    conn = get_connection()

    conn.execute(
        """INSERT INTO scraped_books
        (title, price, rating, availability, source_url, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (
            title,
            price,
            rating,
            availability,
            source_url,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )

    conn.commit()
    conn.close()


def get_all_scraped_books():
    # Mengambil seluruh data hasil scraping
    conn = get_connection()

    rows = conn.execute(
        "SELECT * FROM scraped_books ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return [dict(r) for r in rows]


def get_scraped_book(book_id):
    # Mengambil satu data berdasarkan ID
    conn = get_connection()

    row = conn.execute(
        "SELECT * FROM scraped_books WHERE id=?",
        (book_id,),
    ).fetchone()

    conn.close()

    return dict(row) if row else None


def update_scraped_book(book_id, title, price, rating, availability):
    # Memperbarui data buku hasil scraping
    conn = get_connection()

    conn.execute(
        "UPDATE scraped_books SET title=?, price=?, rating=?, availability=? WHERE id=?",
        (title, price, rating, availability, book_id),
    )

    conn.commit()
    conn.close()


def delete_scraped_book(book_id):
    # Menghapus data hasil scraping berdasarkan ID
    conn = get_connection()

    conn.execute(
        "DELETE FROM scraped_books WHERE id=?",
        (book_id,),
    )

    conn.commit()
    conn.close()


# =======================================================================
# FITUR 2: CRUD tabel koleksi_buku (hasil API)
# =======================================================================

def insert_koleksi(title, authors, published_year, isbn, cover_url, description):
    # Menambahkan buku hasil API ke koleksi pribadi
    conn = get_connection()

    conn.execute(
        """INSERT INTO koleksi_buku
        (title, authors, published_year, isbn, cover_url,
        description, status_baca, rating_pribadi,
        catatan_pribadi, added_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            title,
            authors,
            published_year,
            isbn,
            cover_url,
            description,
            "Belum Dibaca",
            0,
            "",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )

    conn.commit()
    conn.close()


def get_all_koleksi():
    # Mengambil seluruh data koleksi buku
    conn = get_connection()

    rows = conn.execute(
        "SELECT * FROM koleksi_buku ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return [dict(r) for r in rows]


def get_koleksi(koleksi_id):
    # Mengambil satu data koleksi berdasarkan ID
    conn = get_connection()

    row = conn.execute(
        "SELECT * FROM koleksi_buku WHERE id=?",
        (koleksi_id,),
    ).fetchone()

    conn.close()

    return dict(row) if row else None


def is_already_saved(isbn, title):
    # Mengecek apakah buku sudah tersimpan di database
    conn = get_connection()

    if isbn and isbn != "-":
        row = conn.execute(
            "SELECT id FROM koleksi_buku WHERE isbn=?",
            (isbn,),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT id FROM koleksi_buku WHERE title=?",
            (title,),
        ).fetchone()

    conn.close()

    return row is not None


def update_koleksi(koleksi_id, status_baca, rating_pribadi, catatan_pribadi):
    # Memperbarui status baca, rating, dan catatan buku
    conn = get_connection()

    conn.execute(
        """UPDATE koleksi_buku
        SET status_baca=?, rating_pribadi=?, catatan_pribadi=?
        WHERE id=?""",
        (
            status_baca,
            rating_pribadi,
            catatan_pribadi,
            koleksi_id,
        ),
    )

    conn.commit()
    conn.close()


def delete_koleksi(koleksi_id):
    # Menghapus buku dari koleksi
    conn = get_connection()

    conn.execute(
        "DELETE FROM koleksi_buku WHERE id=?",
        (koleksi_id,),
    )

    conn.commit()
    conn.close()


# =======================================================================
# Dashboard
# =======================================================================

def get_dashboard_stats():
    # Mengambil statistik ringkas untuk dashboard
    conn = get_connection()

    # Menghitung jumlah data hasil scraping
    total_scraped = conn.execute(
        "SELECT COUNT(*) c FROM scraped_books"
    ).fetchone()["c"]

    # Menghitung jumlah buku pada koleksi
    total_koleksi = conn.execute(
        "SELECT COUNT(*) c FROM koleksi_buku"
    ).fetchone()["c"]

    # Menghitung jumlah buku berdasarkan status bacaan
    status_rows = conn.execute(
        """
        SELECT status_baca, COUNT(*) c
        FROM koleksi_buku
        GROUP BY status_baca
        """
    ).fetchall()

    status_breakdown = {
        row["status_baca"]: row["c"]
        for row in status_rows
    }

    # Menghitung rata-rata rating pribadi
    avg_row = conn.execute(
        """
        SELECT AVG(rating_pribadi) a
        FROM koleksi_buku
        WHERE rating_pribadi > 0
        """
    ).fetchone()

    avg_rating = round(avg_row["a"], 1) if avg_row["a"] else 0

    conn.close()

    # Mengembalikan seluruh statistik dashboard
    return {
        "total_scraped": total_scraped,
        "total_koleksi": total_koleksi,
        "status_breakdown": status_breakdown,
        "avg_rating": avg_rating,
    }
