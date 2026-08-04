# Mengimpor library requests untuk mengakses API
import requests

# URL endpoint Open Library Search API
SEARCH_URL = "https://openlibrary.org/search.json"

# Header request sebagai identitas aplikasi
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; KatalogBukuApp/1.0)"}


def search_books_api(query, max_results=10):
    # Fungsi untuk mencari buku berdasarkan kata kunci
    debug_info = {"query": query}

    # Validasi agar kata kunci tidak kosong
    if not query.strip():
        debug_info["error"] = "Kata kunci kosong"
        return [], debug_info

    # Parameter yang dikirim ke API
    params = {"q": query, "limit": max_results}

    try:
        # Mengirim request GET ke Open Library API
        response = requests.get(
            SEARCH_URL,
            params=params,
            headers=HEADERS,
            timeout=10
        )
    except requests.RequestException as e:
        # Menangani error jika koneksi ke API gagal
        debug_info["error"] = f"Gagal terhubung ke API: {e}"
        return [], debug_info

    # Menyimpan informasi response untuk debugging
    debug_info["status_code"] = response.status_code
    debug_info["url_dipanggil"] = response.url

    # Memastikan request berhasil (HTTP 200)
    if response.status_code != 200:
        debug_info["error"] = (
            f"API mengembalikan status HTTP {response.status_code} (bukan 200)"
        )
        debug_info["response_snippet"] = response.text[:300]
        return [], debug_info

    try:
        # Mengubah response menjadi format JSON
        data = response.json()
    except ValueError:
        # Menangani jika response bukan JSON
        debug_info["error"] = "Respons API bukan format JSON yang valid"
        debug_info["response_snippet"] = response.text[:300]
        return [], debug_info

    # Mengambil daftar buku dari hasil pencarian
    docs = data.get("docs", [])

    # Menyimpan jumlah total hasil pencarian
    debug_info["total_ditemukan_api"] = data.get("numFound", 0)

    # List untuk menyimpan data buku yang telah diproses
    results = []

    # Memproses setiap buku yang diperoleh dari API
    for doc in docs[:max_results]:

        # Mengambil judul buku
        title = doc.get("title", "Tanpa Judul")

        # Mengambil nama penulis
        authors = ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "Tidak diketahui"

        # Mengambil tahun pertama diterbitkan
        published_year = str(doc.get("first_publish_year", "-"))

        # Mengambil ISBN pertama jika tersedia
        isbn_list = doc.get("isbn", [])
        isbn = isbn_list[0] if isbn_list else "-"

        # Membuat URL cover buku
        cover_id = doc.get("cover_i")
        cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else ""

        # Mengambil deskripsi buku
        first_sentence = doc.get("first_sentence")

        if isinstance(first_sentence, list):
            # Jika deskripsi berupa list, ambil elemen pertama
            description = first_sentence[0] if first_sentence else "Tidak ada deskripsi."

        elif first_sentence:
            # Jika deskripsi berupa string
            description = first_sentence

        else:
            # Jika tidak ada deskripsi, gunakan subject sebagai alternatif
            subjects = doc.get("subject", [])
            description = (
                "Tema: " + ", ".join(subjects[:5])
                if subjects else "Tidak ada deskripsi."
            )

        # Menyimpan data buku ke dalam list hasil
        results.append({
            "title": title,
            "authors": authors,
            "published_year": published_year,
            "isbn": isbn,
            "cover_url": cover_url,
            "description": description,
        })

    # Memberikan informasi jika tidak ada hasil pencarian
    if not results:
        debug_info["error"] = "Tidak ada buku yang cocok dengan kata kunci ini"

    # Mengembalikan data buku beserta informasi debugging
    return results, debug_info
