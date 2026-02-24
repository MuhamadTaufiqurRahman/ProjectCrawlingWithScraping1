import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class BaseScraper:

    def __init__(self, base_url, json_file="hasil.json"):

        self.base_url = base_url
        self.json_file = json_file

        self.all_product_urls = []
        self.all_products = []

        # Nonaktifkan proxy
        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''
        os.environ['NO_PROXY'] = '*'


    def setup_driver(self):

        chrome_options = Options()

        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-proxy-server')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')

        driver = webdriver.Chrome(options=chrome_options)

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