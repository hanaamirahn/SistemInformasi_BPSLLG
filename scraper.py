"""
scraper.py
Web scraping untuk studi kasus KATALOG BUKU.
Sumber: https://books.toscrape.com (situs resmi untuk latihan scraping, legal).

Mengambil data dasar: judul, harga, rating (bintang), status stok, dan URL sumber.
Data pelengkap (penulis, tahun terbit, deskripsi) TIDAK diambil di sini —
itu tugas api_client.py yang menarik dari Open Library API.
"""

import requests
from bs4 import BeautifulSoup
import db

BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"

# Konversi class rating (dalam HTML) ke angka, biar enak dibaca
RATING_MAP = {"One": "1", "Two": "2", "Three": "3", "Four": "4", "Five": "5"}


def scrape_books(pages=1):
    """
    Scrape data buku dari books.toscrape.com sebanyak `pages` halaman,
    lalu simpan ke tabel `books`. Mengembalikan jumlah data yang berhasil disimpan.
    """
    total_saved = 0

    for page in range(1, pages + 1):
        url = BASE_URL.format(page)
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            break  # halaman sudah habis

        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.find_all("article", class_="product_pod")

        if not articles:
            break

        for art in articles:
            title = art.find("h3").find("a")["title"]
            price = art.find("p", class_="price_color").get_text(strip=True)

            rating_class = art.find("p", class_="star-rating")["class"]
            rating_word = [c for c in rating_class if c != "star-rating"][0]
            rating = RATING_MAP.get(rating_word, "-")

            availability = art.find("p", class_="instock availability").get_text(strip=True)
            relative_link = art.find("h3").find("a")["href"]
            source_url = "https://books.toscrape.com/catalogue/" + relative_link.replace("../../../", "")

            db.insert_book(title, price, rating, availability, source_url)
            total_saved += 1

    return total_saved
