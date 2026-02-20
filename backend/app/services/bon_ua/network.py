import cloudscraper
import time

def fetch_html(url, retries=3, timeout=15):
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    
    for attempt in range(retries):
        try:
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
