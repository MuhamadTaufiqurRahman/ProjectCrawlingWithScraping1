import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class BaseScraper:

    def __init__(self, base_url, json_file):

        self.base_url = base_url # simpan base URL
        self.json_file = json_file # simpan nama file output

        self.all_product_urls = [] # list menyimpan URL produk
        self.all_products = [] # list menyimpan hasil scraping (data)

        # Nonaktifkan proxy
        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''
        os.environ['NO_PROXY'] = '*'


    # membuat dan mengembalikan Selenium Chrome driver.
    def setup_driver(self):

        chrome_options = Options()

        # Gunakan headless baru (lebih natural)
        chrome_options.add_argument("--headless=new")

        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--no-proxy-server")

        # 🔥 HILANGKAN AUTOMATION FLAG
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # 🔥 RANDOM USER AGENT
        import random

        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        ]

        chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")

        driver = webdriver.Chrome(options=chrome_options)

        # 🔥 REMOVE navigator.webdriver
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        return driver


    def save_progress(self):

        with open(self.json_file, 'w', encoding='utf-8') as f:

            json.dump(self.all_products, f, indent=2, ensure_ascii=False)

        print(f"Progress saved: {len(self.all_products)} produk")


    # Method ini WAJIB dioverride
    def get_product_urls_from_page(self, page_url):

        raise NotImplementedError


    # Method ini WAJIB dioverride
    def scrape_product(self, url):

        raise NotImplementedError