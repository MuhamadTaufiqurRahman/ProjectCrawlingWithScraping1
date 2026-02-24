import time     # delay agar tidak kena block
import re       # manipulasi text dengan regex (ambil angka dari harga)
import requests         # ambil HTML halaman list produk
from bs4 import BeautifulSoup       # parsing HTML
from selenium.webdriver.common.by import By 
from concurrent.futures import ThreadPoolExecutor, as_completed         # scraping paralel (multi-thread)

from scrapers.base_scraper import BaseScraper 


class WatchesTraderScraper(BaseScraper):

    # kontruksi
    def __init__(self):

        super().__init__(
            base_url="https://watchestrader.id/product/all",
            json_file="dataScraping_watchestrader.json"
        )

        self.start_page = 1             # set halaman awal
        self.max_pages = 3              # set Max Halaman
        self.max_workers = 3            # set jumlah tugas per eksekusi


    # mengambil semua URL produk dari halaman list
    def get_product_urls_from_page(self, page_url):

        try:

            print(f"Mengambil URL dari: {page_url}")

            response = requests.get(page_url)

            soup = BeautifulSoup(response.text, "html.parser")

            # cari semua link produk
            links = soup.find_all(
                "a",
                class_="border-[#eee] border p-3"
            )

            urls = []

            for link in links: # loop setiap link

                # ambil href
                url = link.get("href")

                if url:

                    # ubah jadi full URL
                    if not url.startswith("http"):

                        url = "https://watchestrader.id" + url

                    urls.append(url)    # simpan ke list (urls)

            print(f"Ditemukan {len(urls)} produk")

            return urls

        except Exception as e:

            print("Error:", e)

            return []


    # method scrape product
    def scrape_product(self, url):

        print(f"\nScraping: {url}")

        driver = self.setup_driver()

        try:

            driver.get(url)         # pergi ke URL

            time.sleep(2)

            # scroll sedikit
            driver.execute_script(
                "window.scrollTo(0, 500);"
            )

            time.sleep(0.5)

            # klik tab Specification dan History
            for tab_name in ["SPECIFICATION", "HISTORY"]:

                try:

                    driver.execute_script(f"""
                        var buttons =
                        document.querySelectorAll('button');

                        for(var i=0;i<buttons.length;i++) {{

                            if(buttons[i].textContent
                               .includes('{tab_name}')) {{

                                var parent =
                                buttons[i].parentElement;

                                if(parent &&
                                   parent.getAttribute
                                   ('data-state')
                                   === 'closed') {{

                                    buttons[i].click();
                                    break;
                                }}
                            }}
                        }}
                    """)

                    time.sleep(1)

                except:

                    pass

            # scroll sampai bawah
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )

            time.sleep(1)

            # ambil HTML
            soup = BeautifulSoup(
                driver.page_source,
                "html.parser"
            )

            # buat struktur data (Template output)
            data = {

                "url": url,
                "title": None,
                "price": None,
                "sku": None,
                "brand": None,
                "reference": None,
                "condition": None,
                "year": None,
                "location": None,
                "description": None,
            }

            # ambil title
            title = soup.find("h1")

            if title:

                data["title"] = title.text.strip()

            # ambil harga
            price = soup.find(
                "h4",
                class_="text-xl font-semibold"
            )

            # rubah harga String to Int
            if price:

                price_int = re.sub(
                    r"[^\d]",
                    "",
                    price.text
                )

                if price_int:

                    data["price"] = int(price_int)

            # ambil semua row info
            rows = soup.find_all(
                "div",
                class_=re.compile(r"py-2 flex gap-3")
            )

            # loop semua row
            for row in rows:

                label_p = (
                    row.find("p",
                    class_="w-24 font-medium")
                    or
                    row.find("p",
                    class_="w-36 font-medium")
                )

                if not label_p:

                    continue

                # ambil data pada label (sku, brands, reference, dll)
                label = label_p.text.strip()

                all_p = row.find_all("p")

                if len(all_p) >= 2:

                    value = all_p[1].text.strip()

                    if label == "SKU:":

                        data["sku"] = value

                    elif label == "Brands:":

                        data["brand"] = value

                    elif label == "Reference:":

                        data["reference"] = value

                    elif label == "Condition:":

                        data["condition"] = value

                    elif label == "Year:":

                        data["year"] = value

                    elif label == "Availability:":

                        data["location"] = value

            # ambil description
            desc = soup.find(
                "div",
                class_="text-[#6A6A6A]"
            )

            if desc:

                data["description"] = desc.text.strip()

            return data

        finally:

            driver.quit()


    def run(self):

        print("\n=== WatchesTrader Scraper ===")

        # loop tiap page
        for page in range(
            self.start_page,
            self.start_page + self.max_pages
        ):

            page_url = f"{self.base_url}?page={page}"       # buat url halaman

            # ambil url produk dan simpan ke list utama (urls)
            urls = self.get_product_urls_from_page(
                page_url
            )

            if not urls:

                break

            self.all_product_urls.extend(urls)

            time.sleep(2)

        print(
            f"Total URL: {len(self.all_product_urls)}"
        )

        # jalankan scraping paralel
        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:

            futures = {

                executor.submit(
                    self.scrape_product,
                    url
                ): url

                for url in self.all_product_urls
            }

            for future in as_completed(futures):

                # ambil hasil
                result = future.result()

                if result:

                    self.all_products.append(result)

                    if len(self.all_products) % 5 == 0:

                        self.save_progress()

        # final save
        self.save_progress()

        print("WatchesTrader selesai")