import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .network import fetch_html
from .config import BASE_URL, LISTINGS_URL

from app.services.meget.utils import find_price_by_regex
from app.services.cities import normalize_city
from app.services.address_normalizer import AddressNormalizer


def get_listing_urls(page=1):
    """
    Scrape the listing page on bon.ua to find individual property URLs.
    """
    url = f"{LISTINGS_URL}?page={page}"
    print(f"    Fetching Bon.ua listing page: {url}")
    html = fetch_html(url)
    
    if not html:
        return []
        
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('div.msg-inner')
    
    urls = []
    seen = set()
    
    for card in cards:
        link_elem = card.select_one('a.w-image[href*="/obyavlenie/"]') or card.select_one('a[href*="/obyavlenie/"]')
        if not link_elem:
            continue
            
        href = link_elem.get('href')
        if not href:
            continue
            
        full_url = urljoin(BASE_URL, href)
        if full_url not in seen:
            seen.add(full_url)
            urls.append(full_url)
            
    return urls


class BonUaParser:
    def __init__(self, html, url):
        self.soup = BeautifulSoup(html, 'html.parser')
        self.url = url
        self.page_text = self.soup.get_text(" ", strip=True)
        self.title = self._get_title()

    def _get_title(self):
        title_tag = self.soup.find('h1')
        return title_tag.text.strip() if title_tag else "No Title"

    def get_price_data(self):
        price = 0.0
        currency = "UAH"

        # Try to find a prominent price block first
        price_wrap = self.soup.select_one('.price-wrap, .m-price-wrap, .price')
        if price_wrap:
            text = price_wrap.get_text(" ", strip=True)
            m = re.search(r'(\d+(?:\s+\d+)*)\s*(грн|uah|\$|€|usd|eur)', text, re.IGNORECASE)
            if m:
                amount_str = m.group(1).replace(' ', '')
                curr_str = m.group(2).lower()
                price = float(amount_str)
                if '$' in curr_str or 'usd' in curr_str:
                    currency = "USD"
                elif '€' in curr_str or 'eur' in curr_str:
                    currency = "EUR"
                return price, currency

        # Fallback to general text regex for UAH
        if price == 0.0:
            price = find_price_by_regex(self.page_text, r'(\d[\d\s]*)\s*грн')
            if price > 0:
                return price, "UAH"

        # Fallback for USD
        if price == 0.0:
            price = find_price_by_regex(self.page_text, r'(\d[\d\s]*)\s*\$')
            if price > 0:
                return price, "USD"

        return price, currency

    def get_specs(self):
        rooms = None
        area = None

        # Verbal replacements for rooms
        verbal = {'одно': 1, 'дво': 2, 'три': 3, 'чотири': 4, 'п\'яти': 5, 'шести': 6}
        for k, v in verbal.items():
            if f'{k}кімнатн' in self.title.lower() or f'{k}комнатн' in self.title.lower():
                rooms = v
                break

        if not rooms:
            # Explicit long patterns first (кімнат/комнат), then к/ком/кім with strict boundaries.
            # The '3-х комнатну' case: match digit + optional 'х ' + комнат.
            # Negative: exclude кв.м (кв = square metre) and квартал.
            m = re.search(
                r'(\d+)[\s\-]*(?:х\s*)?(?:кімнат\w*|комнат\w*)',
                self.title, re.IGNORECASE
            )
            if not m:
                m = re.search(
                    r'(\d+)\s*[-]?\s*(?:кім|ком|к)(?!\u0432|\u043a\u0432\u0430\u0440)(?:\b|\s|-)',
                    self.title, re.IGNORECASE
                )
            if m:
                candidate = int(m.group(1))
                if 1 <= candidate <= 10:
                    rooms = candidate

        if not rooms:
            # Structured data fallback: look for 'Кількість кімнат' in page lists
            for li in self.soup.select('li'):
                text = li.get_text(" ", strip=True)
                if 'Кількість кімнат' in text or 'Кімнат' in text:
                    m = re.search(r'(\d+)', text)
                    if m:
                        candidate = int(m.group(1))
                        if 1 <= candidate <= 10:
                            rooms = candidate
                        break

        # Robust regex for Area
        for li in self.soup.select('li, table tr'):
            text = li.get_text(" ", strip=True)
            if 'Загальна площа' in text or 'Площа' in text:
                m = re.search(r'(\d+(?:[\.,]\d+)?)', text.replace('Загальна площа', '').replace('Площа', ''))
                if m:
                    try:
                        area = float(m.group(1).replace(',', '.'))
                        break
                    except ValueError: 
                        pass
                    
        if not area:
            area_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*(?:кв\.?м|м2)', self.page_text, re.IGNORECASE)
            if area_match:
                try:
                    area = float(area_match.group(1).replace(',', '.'))
                except ValueError:
                    pass

        return rooms, area

    def get_location(self):
        city = None
        district = None
        region = None
        
        # In bon.ua, breadcrumbs often contain GEO
        breadcrumbs = self.soup.select('.breadcrumbs a, .breadcrumb a, [class*="bread"] a')
        crumbs_text = [a.get_text(strip=True) for a in breadcrumbs]
        
        for crumb in crumbs_text:
            if "область" in crumb.lower():
                if "-" in crumb:
                    region = crumb.split("-")[-1].strip()
                else:
                    region = crumb.strip()
                continue
                
            if "р-н" in crumb.lower() or "район" in crumb.lower():
                if not district:
                    district = crumb
                continue
                
            normalized = normalize_city(crumb)
            if normalized and not city:
                city = normalized

        # Try to pull from text if breadcrumbs fail
        if not city:
            for word in self.title.split():
                normalized = normalize_city(word.strip('.,!?-'))
                if normalized:
                    city = normalized
                    break

        # Attempt to clean title for address
        cleaned_title = re.sub(r'(Продажа|Продам).*?(квартиры|квартиру)', '', self.title, flags=re.IGNORECASE)
        address = AddressNormalizer.extract_from_text(cleaned_title)
        
        if not address:
            address = AddressNormalizer.extract_from_text(self.page_text)
            
        if city and address and city not in address:
            address = f"{city}, {address}"
        elif city and not address:
            address = city

        return address, city, district, region

    def get_images(self):
        seen = set()
        images = []
        # Usually properties have main images in class="fotorama" or data-fancybox
        img_tags = self.soup.select('.gallery img, .slider img, .fotorama img, .item-image img, img[data-src]')
        
        for img in img_tags:
            src = img.get('src') or img.get('data-src') or img.get('data-newsrc')
            if not src: 
                continue
            
            # Skip tiny icons
            if any(skip in src.lower() for skip in ['icon', 'logo', 'avatar', 'banner', 'svg']):
                continue
                
            full_url = urljoin(self.url, src)
            if full_url not in seen:
                seen.add(full_url)
                images.append(full_url)
                
        # If no images found, try og:image
        if not images:
            og_img = self.soup.find('meta', property='og:image')
            if og_img and og_img.get('content'):
                images.append(urljoin(self.url, og_img.get('content')))

        return images

    def parse(self):
        price, currency = self.get_price_data()
        rooms, area = self.get_specs()
        address, city, district, region = self.get_location()
        images = self.get_images()

        return {
            "source_url": self.url,
            "source_website": "bon_ua",
            "title": self.title,
            "price": price,
            "currency": currency,
            "address": address,
            "city": city,
            "district": district,
            "region": region,
            "area": area,
            "rooms": rooms,
            "images": images
        }
