import sys # Import module sys untuk membaca argument dari command line.

# Import class scraper yang sudah di buat.
from scrapers.aristo_scraper import AristoScraper
from scrapers.watchestrader_scraper import WatchesTraderScraper
from scrapers.luxehouze_scraper import LuxehouzeScraper

# function utama pengontrol scraper
def main():

    # cek perintah
    if len(sys.argv) < 2:
        print("Usage:")
        print("python3 main.py aristo")
        print("python3 main.py watches")
        print("python3 main.py luxehouze")
        print("python3 main.py all")
        return

    # ambil parameter dari command line
    target = sys.argv[1]

    # jalankan scraper sesuai parameter yang diambil
    if target == "aristo":
        AristoScraper().run()

    elif target == "watches":
        WatchesTraderScraper().run()

    elif target == "luxehouze":
        LuxehouzeScraper().run()

    elif target == "all":
        AristoScraper().run()
        WatchesTraderScraper().run()
        LuxehouzeScraper().run()

    else:
        print("Target tidak dikenal")


if __name__ == "__main__":
    main()