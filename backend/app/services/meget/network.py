import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .config import BASE_URL, HEADERS


def fetch_html(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return BeautifulSoup(response.content, 'html.parser')
    except Exception:
        pass
    return None


def get_listing_urls(page=1):
    url = f"{BASE_URL}show/{page}/" if page > 1 else BASE_URL
    soup = fetch_html(url)

    if not soup:
        return []

    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if '/prodazha-kvartir/details/' in href or '/sale/flat/details/' in href:
            full_url = urljoin("https://meget.kiev.ua", href)
            links.add(full_url)

    return list(links)