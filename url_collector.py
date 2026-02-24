import requests
from bs4 import BeautifulSoup


def get_product_urls_from_page(page_url):

    try:

        print(f"  Mengambil URL dari: {page_url}")

        response = requests.get(page_url)

        soup = BeautifulSoup(response.text, "html.parser")

        products = soup.select("div.my-12.grid > div.flex.flex-col")

        urls = []

        for product in products:

            link = product.find("a", href=True)

            if not link:

                continue

            url = link["href"]

            if not url.startswith("http"):

                url = "https://aristohk.com" + url

            urls.append(url)

            print("  ditemukan:", url)

        print(f"Total ditemukan: {len(urls)} produk")

        return urls

    except Exception as e:

        print("Error:", e)

        return []