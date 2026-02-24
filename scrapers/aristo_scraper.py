import time
import re
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from concurrent.futures import ThreadPoolExecutor, as_completed

from scrapers.base_scraper import BaseScraper


class AristoScraper(BaseScraper):

    def __init__(self):

        super().__init__(
            base_url="https://aristohk.com/new-watch",
            json_file="dataScraping_aristohk.json"
        )

        self.start_page = 1
        self.max_pages = 5
        self.max_workers = 3


    def get_product_urls_from_page(self, page_url):

        try:

            print(f"Mengambil URL dari: {page_url}")

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

                print(" ditemukan:", url)

            print(f"Total ditemukan: {len(urls)}")

            return urls

        except Exception as e:

            print("Error:", e)

            return []


    def scrape_product(self, url):

        print(f"\nScraping: {url}")

        driver = self.setup_driver()

        try:

            driver.get(url)

            time.sleep(2)

            driver.execute_script("window.scrollTo(0, 500);")

            time.sleep(1)

            try:

                desc_button = driver.find_element(
                    By.XPATH,
                    "//button[normalize-space()='Description']"
                )

                driver.execute_script(
                    "arguments[0].click();",
                    desc_button
                )

                time.sleep(1)

                print("Tab Description diklik")

            except:

                print("Tab Description tidak ditemukan")

            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )

            time.sleep(1)

            soup = BeautifulSoup(
                driver.page_source,
                "html.parser"
            )

            data = {
                "url": url,
                "title": None,
                "price": None,
                "description": None
            }

            title = soup.find("h1")

            if title:

                data["title"] = title.get_text(strip=True)

                print("Title:", data["title"])

            rows = soup.select("div.flex.items-center")

            for row in rows:

                text = row.get_text(strip=True)

                if ":" not in text:
                    continue

                key, value = text.split(":", 1)

                key = key.lower().strip().replace(" ", "_")

                value = value.strip()

                if key == "retail_price":

                    price_int = re.sub(r"[^\d]", "", value)

                    if price_int:

                        data["price"] = int(price_int)

                        print("Price:", data["price"])

                else:

                    data[key] = value

            sections = soup.select("div.grid.grid-cols-6")

            for section in sections:

                cells = section.select("div.col-span-3")

                for i in range(0, len(cells), 2):

                    try:

                        label = cells[i].get_text(strip=True)

                        value = cells[i+1].get_text(strip=True)

                        key = label.lower().replace(" ", "_")

                        if key == "release_year":

                            year = re.sub(r"[^\d]", "", value)

                            if year:

                                data[key] = int(year)

                        else:

                            data[key] = value

                    except:

                        pass

            desc = soup.select_one(
                "div[role='tabpanel'] div.py-4"
            )

            if desc:

                data["description"] = desc.get_text(strip=True)

            return data

        finally:

            driver.quit()


    def run(self):

        print("Memulai Aristo Scraper")

        for page in range(
            self.start_page,
            self.start_page + self.max_pages
        ):

            print(f"\nHALAMAN {page}")

            page_url = f"{self.base_url}?page={page}"

            urls = self.get_product_urls_from_page(page_url)

            if not urls:
                break

            self.all_product_urls.extend(urls)

            time.sleep(2)

        print(f"\nTotal URL: {len(self.all_product_urls)}")

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

                    print("Success:",
                          result.get("title"))

                    if len(self.all_products) % 5 == 0:

                        self.save_progress()

        self.save_progress()

        print("Scraping selesai")