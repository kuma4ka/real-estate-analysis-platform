import cloudscraper
import time

def fetch_html(url, retries=3, timeout=15):
    # Try different configurations across retries
    configs = [
        {'browser': 'chrome', 'platform': 'windows', 'mobile': False},
        {'browser': 'firefox', 'platform': 'linux', 'mobile': False},
        {'custom': 'ScraperBot/1.0'}
    ]

    for attempt in range(retries):
        try:
            cfg = configs[attempt % len(configs)]
            scraper = cloudscraper.create_scraper(browser=cfg)
            response = scraper.get(url, timeout=timeout)
            
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                print(f"[{attempt+1}/{retries}] 404 Not Found: {url}")
                return None
            else:
                print(f"[{attempt+1}/{retries}] Status {response.status_code} for {url}")
        except Exception as e:
            print(f"[{attempt+1}/{retries}] Error fetching {url}: {e}")
            
        time.sleep(2 * (attempt + 1))
        
    return None
