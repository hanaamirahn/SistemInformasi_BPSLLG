"""
api_client.py
Konsumsi API untuk studi kasus KATALOG BUKU.
Sumber: Open Library Search API (https://openlibrary.org/search.json)
API publik gratis, tidak butuh API key.

Fungsi ini MELENGKAPI data buku yang sudah ada di tabel `books` (hasil scraping),
bukan membuat data baru yang berdiri sendiri. Pencarian dilakukan berdasarkan
judul buku, hasilnya disimpan ke tabel `book_enrichment` dengan relasi book_id.
"""

import requests
import db

SEARCH_URL = "https://openlibrary.org/search.json"


def enrich_book(book_id):
    """
    Ambil data pelengkap (penulis, tahun terbit, subjek, deskripsi singkat)
    dari Open Library berdasarkan judul buku dengan id `book_id`,
    lalu simpan/ubah di tabel book_enrichment.

    Return: dict data yang disimpan, atau None kalau tidak ditemukan / gagal.
    """
    book = db.get_book(book_id)
    if not book:
        return None

    params = {"title": book["title"], "limit": 1}
    response = requests.get(SEARCH_URL, params=params, timeout=10)

    if response.status_code != 200:
        return None

    data = response.json()
    docs = data.get("docs", [])
    if not docs:
        return None

    doc = docs[0]
    author = ", ".join(doc.get("author_name", [])) or "-"
    first_publish_year = str(doc.get("first_publish_year", "-"))
    subjects = ", ".join(doc.get("subject", [])[:5]) if doc.get("subject") else "-"
    description = doc.get("first_sentence", ["-"])
    if isinstance(description, list):
        description = description[0] if description else "-"

    db.upsert_enrichment(book_id, author, first_publish_year, subjects, description)

    return {
        "author": author,
        "first_publish_year": first_publish_year,
        "subjects": subjects,
        "description": description,
    }
