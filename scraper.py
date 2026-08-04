"""
scraper.py
FITUR 1: Web Scraping.

Mengambil data buku dari website:
https://books.toscrape.com

Data yang diambil:
- Judul
- Harga
- Rating
- Status stok
- URL sumber

Data hasil scraping disimpan ke tabel `scraped_books`.
"""

# Library untuk mengirim HTTP request ke website
import requests

# Library untuk membaca dan mengekstrak data HTML
from bs4 import BeautifulSoup

# Modul database untuk menyimpan hasil scraping
import db

# URL halaman buku (nomor halaman akan diganti secara otomatis)
BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"

# Konversi rating dari teks menjadi angka
RATING_MAP = {
    "One": "1",
    "Two": "2",
    "Three": "3",
    "Four": "4",
    "Five": "5"
}


def scrape_books(pages=1):
    """
    Mengambil data buku dari beberapa halaman website.

    Parameter:
    pages : jumlah halaman yang akan di-scrape

    Return:
    total_saved : jumlah data yang berhasil disimpan
    """

    # Menghitung jumlah buku yang berhasil disimpan
    total_saved = 0

    # Melakukan scraping sebanyak jumlah halaman yang diminta
    for page in range(1, pages + 1):

        # Membentuk URL sesuai nomor halaman
        url = BASE_URL.format(page)

        # Mengirim request ke website
        response = requests.get(url, timeout=10)

        # Menghentikan proses jika halaman tidak dapat diakses
        if response.status_code != 200:
            break

        # Mengubah HTML menjadi objek BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Mengambil seluruh data buku pada halaman
        articles = soup.find_all("article", class_="product_pod")

        # Menghentikan proses jika tidak ada data buku
        if not articles:
            break

        # Memproses setiap buku yang ditemukan
        for art in articles:

            # Mengambil judul buku
            title = art.find("h3").find("a")["title"]

            # Mengambil harga buku
            price = art.find(
                "p",
                class_="price_color"
            ).get_text(strip=True)

            # Mengambil class rating (One, Two, Three, dst.)
            rating_class = art.find(
                "p",
                class_="star-rating"
            )["class"]

            # Mengambil nilai rating selain class "star-rating"
            rating_word = [
                c for c in rating_class
                if c != "star-rating"
            ][0]

            # Mengubah rating teks menjadi angka
            rating = RATING_MAP.get(rating_word, "-")

            # Mengambil informasi ketersediaan stok
            availability = art.find(
                "p",
                class_="instock availability"
            ).get_text(strip=True)

            # Mengambil URL relatif buku
            relative_link = art.find("h3").find("a")["href"]

            # Mengubah URL relatif menjadi URL lengkap
            source_url = (
                "https://books.toscrape.com/catalogue/"
                + relative_link.replace("../../../", "")
            )

            # Menyimpan data buku ke database
            db.insert_scraped_book(
                title,
                price,
                rating,
                availability,
                source_url
            )

            # Menambah jumlah data yang berhasil disimpan
            total_saved += 1

    # Mengembalikan jumlah buku yang berhasil disimpan
    return total_saved
