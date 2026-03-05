import sys

from scrapers.aristo_scraper import AristoScraper
from scrapers.watchestrader_scraper import WatchesTraderScraper
from scrapers.luxehouze_scraper import LuxehouzeScraper


def main():

    if len(sys.argv) < 2:
        print("Usage:")
        print("python3 main.py aristo")
        print("python3 main.py watches")
        print("python3 main.py luxehouze")
        print("python3 main.py all")
        return

    target = sys.argv[1]

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