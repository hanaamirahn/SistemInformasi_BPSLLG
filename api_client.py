"""
api_client.py
FITUR 2: Tarik data dari API.
Sumber: Open Library Search API (https://openlibrary.org/search.json)
Gratis, TIDAK butuh API key, dan tidak punya batas kuota ketat seperti
Google Books API (yang sempat kena "Quota exceeded" saat testing).

search_books_api() mengembalikan (results, debug_info):
- results: list buku yang ditemukan (bisa kosong)
- debug_info: dict berisi status_code, url yang dipanggil, dan pesan error kalau ada
  -> dipakai untuk troubleshooting kalau pencarian gagal terus
"""

import requests

SEARCH_URL = "https://openlibrary.org/search.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; KatalogBukuApp/1.0)"}


def search_books_api(query, max_results=10):
    """
    Cari buku di Open Library berdasarkan kata kunci `query`.
    Return: (results, debug_info)
    """
    debug_info = {"query": query}

    if not query.strip():
        debug_info["error"] = "Kata kunci kosong"
        return [], debug_info

    params = {"q": query, "limit": max_results}

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

    docs = data.get("docs", [])
    debug_info["total_ditemukan_api"] = data.get("numFound", 0)

    results = []
    for doc in docs[:max_results]:
        title = doc.get("title", "Tanpa Judul")
        authors = ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "Tidak diketahui"
        published_year = str(doc.get("first_publish_year", "-"))

        isbn_list = doc.get("isbn", [])
        isbn = isbn_list[0] if isbn_list else "-"

        cover_id = doc.get("cover_i")
        cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else ""

        first_sentence = doc.get("first_sentence")
        if isinstance(first_sentence, list):
            description = first_sentence[0] if first_sentence else "Tidak ada deskripsi."
        elif first_sentence:
            description = first_sentence
        else:
            subjects = doc.get("subject", [])
            description = ("Tema: " + ", ".join(subjects[:5])) if subjects else "Tidak ada deskripsi."

        results.append({
            "title": title,
            "authors": authors,
            "published_year": published_year,
            "isbn": isbn,
            "cover_url": cover_url,
            "description": description,
        })

    if not results:
        debug_info["error"] = "Tidak ada buku yang cocok dengan kata kunci ini"

    return results, debug_info
