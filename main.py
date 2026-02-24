import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import BASE_URL, START_PAGE, MAX_PAGES, JSON_FILE, MAX_WORKERS
from scraper import scrape_product_wrapper
from url_collector import get_product_urls_from_page


def main():

    all_product_urls = []

    all_products = []

    print(f"Memulai scraping dengan sistem PAGINATION")

    print(f"Base URL: {BASE_URL}")

    print(f"Start Page: {START_PAGE}")

    print(f"Max Pages: {MAX_PAGES}")

    print("-" * 50)

    for page in range(START_PAGE, START_PAGE + MAX_PAGES):

        print(f"\n=== MEMPROSES HALAMAN {page} ===")

        if '?' in BASE_URL:

            page_url = f"{BASE_URL}&page={page}"

        else:

            page_url = f"{BASE_URL}?page={page}"

        page_urls = get_product_urls_from_page(page_url)

        if not page_urls:

            print(f"Tidak ada produk ditemukan di halaman {page}. Berhenti...")

            break

        all_product_urls.extend(page_urls)

        print(f"Total URL terkumpul: {len(all_product_urls)}")

        if page < START_PAGE + MAX_PAGES - 1:

            time.sleep(2)

    print(f"\n=== TOTAL URL TERKUMPUL: {len(all_product_urls)} ===")

    if not all_product_urls:

        print("Tidak ada URL produk ditemukan.")

        return

    print(f"\nMulai scraping {len(all_product_urls)} produk...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        future_to_url = {

            executor.submit(scrape_product_wrapper, url): url

            for url in all_product_urls

        }

        for i, future in enumerate(as_completed(future_to_url), 1):

            url = future_to_url[future]

            try:

                product_data = future.result()

                if product_data:

                    all_products.append(product_data)

                    print(f"✓ Produk {i}/{len(all_product_urls)} selesai: {product_data.get('title', 'Unknown')}")

                else:

                    print(f"✗ Produk {i} gagal: {url}")

            except Exception as e:

                print(f"✗ Error processing {url}: {e}")

            if len(all_products) % 5 == 0:

                with open(JSON_FILE, 'w', encoding='utf-8') as f:

                    json.dump(all_products, f, indent=2, ensure_ascii=False)

                print(f"\nProgress saved: {len(all_products)} produk ke {JSON_FILE}")

    with open(JSON_FILE, 'w', encoding='utf-8') as f:

        json.dump(all_products, f, indent=2, ensure_ascii=False)

    print(f"\n=== SCRAPING SELESAI ===")

    print(f"Total halaman diproses: {min(page - START_PAGE + 1, MAX_PAGES)}")

    print(f"Total URL dikumpulkan: {len(all_product_urls)}")

    print(f"Total produk berhasil di-scrape: {len(all_products)}")

    print(f"Data disimpan di: {JSON_FILE}")


if __name__ == "__main__":

    main()