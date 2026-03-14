import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .config import HEADERS


def fetch_html(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return BeautifulSoup(response.content, 'html.parser')
    except Exception:
        pass
    return None


def get_listing_urls(base_url, page=1):
    url = f"{base_url}show/{page}/" if page > 1 else base_url
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