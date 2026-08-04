"""
api_client.py
FITUR 2: Mengambil data buku dari Open Library Search API.

API yang digunakan:
https://openlibrary.org/search.json

Keunggulan:
- Gratis
- Tidak memerlukan API Key
- Tidak memiliki batas kuota yang ketat

Fungsi utama:
search_books_api()

Mengembalikan:
1. results     -> daftar buku yang berhasil ditemukan
2. debug_info  -> informasi debugging apabila terjadi error
"""

# Library untuk mengirim HTTP Request ke API
import requests

# Endpoint API Open Library
SEARCH_URL = "https://openlibrary.org/search.json"

# Header request sebagai identitas aplikasi
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; KatalogBukuApp/1.0)"
}


def search_books_api(query, max_results=10):
    """
    Melakukan pencarian buku berdasarkan kata kunci.

    Parameter:
    query        : kata kunci pencarian buku
    max_results  : jumlah maksimum hasil yang ditampilkan

    Return:
    results, debug_info
    """

    # Dictionary untuk menyimpan informasi debugging
    debug_info = {"query": query}

    # Mengecek apakah kata kunci pencarian kosong
    if not query.strip():
        debug_info["error"] = "Kata kunci kosong"
        return [], debug_info

    # Parameter yang akan dikirim ke API
    params = {
        "q": query,          # kata kunci pencarian
        "limit": max_results # jumlah hasil maksimal
    }

    # Mengirim request GET ke Open Library API
    try:
        response = requests.get(
            SEARCH_URL,
            params=params,
            headers=HEADERS,
            timeout=10  # maksimal menunggu respons 10 detik
        )

    # Menangani error jika koneksi gagal
    except requests.RequestException as e:
        debug_info["error"] = f"Gagal terhubung ke API: {e}"
        return [], debug_info

    # Menyimpan status HTTP dan URL request untuk debugging
    debug_info["status_code"] = response.status_code
    debug_info["url_dipanggil"] = response.url

    # Memastikan API mengembalikan status sukses (HTTP 200)
    if response.status_code != 200:
        debug_info["error"] = (
            f"API mengembalikan status HTTP {response.status_code} (bukan 200)"
        )

        # Menyimpan sebagian isi response untuk analisis error
        debug_info["response_snippet"] = response.text[:300]
        return [], debug_info

    # Mengubah response menjadi format JSON
    try:
        data = response.json()

    # Menangani jika response bukan JSON
    except ValueError:
        debug_info["error"] = "Respons API bukan format JSON yang valid"
        debug_info["response_snippet"] = response.text[:300]
        return [], debug_info

    # Mengambil daftar buku dari field "docs"
    docs = data.get("docs", [])

    # Menyimpan jumlah total buku yang ditemukan API
    debug_info["total_ditemukan_api"] = data.get("numFound", 0)

    # List untuk menyimpan hasil pencarian
    results = []

    # Memproses setiap buku yang ditemukan
    for doc in docs[:max_results]:

        # Mengambil judul buku
        title = doc.get("title", "Tanpa Judul")

        # Mengambil nama penulis
        authors = (
            ", ".join(doc.get("author_name", []))
            if doc.get("author_name")
            else "Tidak diketahui"
        )

        # Mengambil tahun pertama diterbitkan
        published_year = str(doc.get("first_publish_year", "-"))

        # Mengambil ISBN pertama apabila tersedia
        isbn_list = doc.get("isbn", [])
        isbn = isbn_list[0] if isbn_list else "-"

        # Mengambil ID cover buku
        cover_id = doc.get("cover_i")

        # Membentuk URL gambar cover
        cover_url = (
            f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
            if cover_id
            else ""
        )

        # Mengambil kalimat pembuka sebagai deskripsi
        first_sentence = doc.get("first_sentence")

        # Jika first_sentence berupa list
        if isinstance(first_sentence, list):
            description = (
                first_sentence[0]
                if first_sentence
                else "Tidak ada deskripsi."
            )

        # Jika berupa string
        elif first_sentence:
            description = first_sentence

        # Jika tidak ada deskripsi, gunakan subject sebagai pengganti
        else:
            subjects = doc.get("subject", [])

            description = (
                "Tema: " + ", ".join(subjects[:5])
                if subjects
                else "Tidak ada deskripsi."
            )

        # Menyimpan informasi buku ke dalam list hasil
        results.append({
            "title": title,
            "authors": authors,
            "published_year": published_year,
            "isbn": isbn,
            "cover_url": cover_url,
            "description": description,
        })

    # Jika tidak ada buku yang ditemukan
    if not results:
        debug_info["error"] = (
            "Tidak ada buku yang cocok dengan kata kunci ini"
        )

    # Mengembalikan hasil pencarian dan informasi debugging
    return results, debug_info
