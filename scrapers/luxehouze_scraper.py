import time
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from scrapers.base_scraper import BaseScraper


class LuxehouzeScraper(BaseScraper):

    def __init__(self):

        super().__init__(
            base_url="https://luxehouze.com/id/en/watch/category/all-watches",
            json_file="dataScraping_luxehouze.json"
        )

        self.max_scroll = 1
        self.scroll_pause = 2
        self.max_workers = 5


    # ambil semua URL produk via infinite scroll
    def get_product_urls_from_page(self, page_url):

        print(f"Membuka halaman: {page_url}")

        driver = self.setup_driver()

        urls = set()

        try:

            driver.get(page_url)

            time.sleep(5)

            last_height = driver.execute_script(
                "return document.body.scrollHeight"
            )

            for i in range(self.max_scroll):

                print(f"Scroll {i+1}")

                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )

                time.sleep(self.scroll_pause)

                soup = BeautifulSoup(
                    driver.page_source,
                    "html.parser"
                )

                cards = soup.select(
                    "div.product-card a[href]"
                )

                for card in cards:

                    url = card.get("href")

                    if url and not url.startswith("http"):
                        url = "https://luxehouze.com" + url

                    if url and "/product/watch/" in url:
                        urls.add(url)

                print("Total URL sementara:", len(urls))

                new_height = driver.execute_script(
                    "return document.body.scrollHeight"
                )

                if new_height == last_height:
                    print("Scroll selesai")
                    break

                last_height = new_height

            return list(urls)

        finally:
            driver.quit()


    # scrape detail produk lengkap
    def scrape_product(self, url):

        print("Scraping:", url)

        driver = self.setup_driver()

        try:

            driver.get(url)

            time.sleep(3)

            # =====================
            # klik DESCRIPTION TAB
            # =====================
            try:

                desc_tab = driver.find_element(
                    By.XPATH,
                    "//button[.//span[contains(text(),'DESCRIPTION')]]"
                )

                driver.execute_script(
                    "arguments[0].click();",
                    desc_tab
                )

                time.sleep(1)

                print("DESCRIPTION diklik")

            except:
                print("DESCRIPTION tidak ditemukan")


            # scroll bawah
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )

            time.sleep(1)


            # =====================
            # klik SHOW MORE
            # =====================
            try:
                show_more_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[.//span[contains(text(),'SHOW MORE')]]")
                    )
                )
                driver.execute_script("arguments[0].click();", show_more_btn)

                # tunggu sampai tombol berubah jadi SHOW LESS
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//span[contains(text(),'SHOW LESS')]")
                    )
                )

                print("SHOW MORE diklik & render selesai")

            except:
                print("SHOW MORE tidak ada")

            
            # parse HTML final
            soup = BeautifulSoup(
                driver.page_source,
                "html.parser"
            )


            # =====================
            # struktur data
            # =====================
            data = {
                "url": url,
                "title": None,
                "price": None,
                "description": None
            }


            # =====================
            # ambil title
            # =====================
            title = soup.find(
                "h2",
                class_="black-7 regular subtitle-2 work-sans svelte-1j3rafz"
            )

            if title:
                data["title"] = title.get_text(strip=True)


            # =====================
            # ambil price
            # =====================
            data["price"] = None
            data["original_price"] = None

            price_spans = soup.find_all("span")

            for span in price_spans:

                text = span.get_text(strip=True)

                if not text.startswith("Rp"):
                    continue

                price_int = re.sub(r"[^\d]", "", text)

                if not price_int:
                    continue

                price_int = int(price_int)

                classes = span.get("class", [])

                if "line-through" in classes:
                    data["original_price"] = price_int
                else:
                    # ambil harga aktif pertama saja
                    if data["price"] is None:
                        data["price"] = price_int


            # scroll sedikit
            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(1)

            # =====================
            # ambil semua specs
            # =====================
            specs = soup.select("div[class*='justify-between']")

            for spec in specs:

                spans = spec.find_all("span")

                if len(spans) != 2:
                    continue

                key = spans[0].get_text(strip=True)\
                    .lower()\
                    .replace(" ", "_")

                value = spans[1].get_text(strip=True)

                data[key] = value


            # =====================
            # ambil description
            # =====================
            desc = soup.select_one(
                "div.leading-relaxed"
            )

            if desc:

                data["description"] = desc.get_text(
                    strip=True
                )


            print("Success:", data["title"])

            return data


        finally:
            driver.quit()


    def run(self):

        print("Memulai Luxehouze Scraper")

        urls = self.get_product_urls_from_page(
            self.base_url
        )

        self.all_product_urls.extend(urls)

        print("Total URL:", len(urls))

        from concurrent.futures import ThreadPoolExecutor, as_completed

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

                result = future.result()

                if result:

                    self.all_products.append(result)

                    if len(self.all_products) % 5 == 0:
                        self.save_progress()

        self.save_progress()

        print("Luxehouze selesai")