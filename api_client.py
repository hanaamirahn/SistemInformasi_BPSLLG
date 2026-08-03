"""
api_client.py
FITUR 2: Tarik data dari API.
Sumber: Google Books API (https://www.googleapis.com/books/v1/volumes)
Gratis, tidak butuh API key untuk penggunaan dasar/pencarian.

search_books_api() mengembalikan (results, debug_info):
- results: list buku yang ditemukan (bisa kosong)
- debug_info: dict berisi status_code, url yang dipanggil, dan pesan error kalau ada
  -> ini dipakai untuk troubleshooting kalau pencarian selalu gagal
"""

import requests

SEARCH_URL = "https://www.googleapis.com/books/v1/volumes"

# Beberapa API menolak request tanpa User-Agent yang jelas (dianggap bot).
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; KatalogBukuApp/1.0)"}


def search_books_api(query, max_results=10):
    """
    Cari buku di Google Books API berdasarkan kata kunci `query`.
    Return: (results, debug_info)
    """
    debug_info = {"query": query}

    if not query.strip():
        debug_info["error"] = "Kata kunci kosong"
        return [], debug_info

    params = {"q": query, "maxResults": max_results}

    try:
        response = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=10)
    except requests.RequestException as e:
        debug_info["error"] = f"Gagal terhubung ke API: {e}"
        return [], debug_info

    debug_info["status_code"] = response.status_code
    debug_info["url_dipanggil"] = response.url

    if response.status_code != 200:
        debug_info["error"] = f"API mengembalikan status HTTP {response.status_code} (bukan 200)"
        debug_info["response_snippet"] = response.text[:300]
        return [], debug_info

    try:
        data = response.json()
    except ValueError:
        debug_info["error"] = "Respons API bukan format JSON yang valid"
        debug_info["response_snippet"] = response.text[:300]
        return [], debug_info

    debug_info["total_items_dilaporkan_api"] = data.get("totalItems", 0)
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

    if not results:
        debug_info["error"] = "API merespons 200 OK, tapi tidak ada 'items' di hasilnya (kata kunci tidak ditemukan)"

    return results, debug_info
