import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin


def get_listing_urls():
    base_url = "https://meget.kiev.ua/prodazha-kvartir/kiev/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print(f"📡 Скануємо каталог: {base_url} ...")
        response = requests.get(base_url, headers=headers)

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        links = set()

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if '/prodazha-kvartir/details/' in href or '/sale/flat/details/' in href:
                full_url = urljoin(base_url, href)
                links.add(full_url)

        print(f"🔎 Знайдено {len(links)} оголошень.")
        return list(links)

    except Exception:
        return []


def scrape_meget_listing(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print(f"📥 Завантажую: {url}")
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"❌ Помилка доступу: {response.status_code}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text(" ", strip=True)

        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else "Без заголовка"

        price_val = 0.0
        currency = "USD"

        price_usd_span = soup.find('span', id='price_usd')
        if price_usd_span:
            price_text = price_usd_span.text.strip()
            clean_price = re.sub(r'[^\d]', '', price_text)
            if clean_price:
                price_val = float(clean_price)
                currency = "USD"
        else:
            price_tag = soup.find('div', class_='price') or soup.find('span', class_='price')
            if price_tag:
                price_text = price_tag.text.strip()
                clean_price = re.sub(r'[^\d]', '', price_text)
                if clean_price:
                    price_val = float(clean_price)
                    if 'грн' in price_text.lower():
                        currency = "UAH"

        rooms = None
        rooms_match = re.search(r'(\d+)\s*[-]?\s*(?:ком|кім)', title, re.IGNORECASE)
        if rooms_match:
            rooms = int(rooms_match.group(1))

        area = None
        area_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*/\s*\d+(?:[\.,]\d+)?\s*/\s*\d+(?:[\.,]\d+)?', page_text)

        if area_match:
            area_str = area_match.group(1).replace(',', '.')
            area = float(area_str)
        else:
            area_text_match = re.search(r'(?:Площадь|Площа)[:\s]+(\d+(?:[\.,]\d+)?)', page_text, re.IGNORECASE)
            if area_text_match:
                area = float(area_text_match.group(1).replace(',', '.'))

        address = None
        address_div = soup.find('div', style=re.compile(r'font-size:\s*1[4-6]px'))
        if address_div:
            address = address_div.text.strip()
        else:
            addr_match = re.search(r'Киев,\s*(.*?)(?:рядом метро|$)', page_text, re.IGNORECASE)
            if addr_match:
                address = addr_match.group(1).strip()

        data = {
            "source_url": url,
            "source_website": "meget",
            "title": title,
            "price": price_val,
            "currency": currency,
            "address": address,
            "area": area,
            "rooms": rooms
        }

        return data

    except Exception as e:
        print(f"❌ Помилка при парсингу: {e}")
        return None