import logging
import cloudscraper
import time

logger = logging.getLogger(__name__)


def fetch_html(url, retries=3, timeout=15):
    configs = [
        {'browser': 'firefox', 'platform': 'linux', 'mobile': False},
        {'browser': 'firefox', 'platform': 'windows', 'mobile': False},
        {'browser': 'chrome', 'platform': 'windows', 'mobile': False},
        {'browser': 'chrome', 'platform': 'linux', 'mobile': False},
    ]

    for attempt in range(retries):
        try:
            cfg = configs[attempt % len(configs)]
            scraper = cloudscraper.create_scraper(browser=cfg)
            response = scraper.get(url, timeout=timeout)

            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                logger.warning("[%d/%d] 404 Not Found: %s", attempt + 1, retries, url)
                return None
            else:
                logger.warning("[%d/%d] Status %s for %s", attempt + 1, retries, response.status_code, url)
        except Exception as e:
            logger.error("[%d/%d] Error fetching %s: %s", attempt + 1, retries, url, e)

        time.sleep(2 * (attempt + 1))

    return None

