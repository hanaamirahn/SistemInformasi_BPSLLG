"""
api_client.py
FITUR 2: Tarik data dari API.
Sumber: Google Books API (https://www.googleapis.com/books/v1/volumes)
Gratis, tidak butuh API key untuk penggunaan dasar/pencarian.

Modul ini HANYA bertugas mencari & mengembalikan data dari API.
Proses simpan ke database dilakukan terpisah oleh app.py lewat db.insert_koleksi(),
supaya user yang menentukan buku mana yang benar-benar mau disimpan ke koleksinya.
"""

import requests

SEARCH_URL = "https://www.googleapis.com/books/v1/volumes"


def search_books_api(query, max_results=10):
    """
    Cari buku di Google Books API berdasarkan kata kunci `query`.
    Return: list of dict, masing-masing berisi title, authors, published_year,
    isbn, cover_url, description. List kosong kalau tidak ada hasil / gagal.
    """
    if not query.strip():
        return []

    params = {"q": query, "maxResults": max_results}

    try:
        response = requests.get(SEARCH_URL, params=params, timeout=10)
    except requests.RequestException:
        return []

    if response.status_code != 200:
        return []

    data = response.json()
    items = data.get("items", [])
    results = []

    for item in items:
        info = item.get("volumeInfo", {})

        title = info.get("title", "Tanpa Judul")
        authors = ", ".join(info.get("authors", [])) if info.get("authors") else "Tidak diketahui"

        published_date = info.get("publishedDate", "")
        published_year = published_date[:4] if published_date else "-"

        isbn = "-"
        for ident in info.get("industryIdentifiers", []):
            if ident.get("type") in ("ISBN_13", "ISBN_10"):
                isbn = ident.get("identifier", "-")
                break

        cover_url = info.get("imageLinks", {}).get("thumbnail", "")
        description = info.get("description", "Tidak ada deskripsi.")

        results.append({
            "title": title,
            "authors": authors,
            "published_year": published_year,
            "isbn": isbn,
            "cover_url": cover_url,
            "description": description,
        })

    return results
