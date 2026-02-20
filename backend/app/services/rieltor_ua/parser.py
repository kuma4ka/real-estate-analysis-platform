import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .config import BASE_URL, LISTINGS_URL
from .network import fetch_html
from app.services.address_normalizer import AddressNormalizer
from app.services.cities import normalize_city

def get_listing_urls(page=1):
    url = f"{LISTINGS_URL}?page={page}"
    print(f"    Fetching Rieltor.ua listing page: {url}")
    html = fetch_html(url)
    
    if not html:
        return []
        
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.select('a[href*="/flats-sale/view/"]')
    
    urls = []
    seen = set()
    
    for link in links:
        href = link.get('href')
        if not href or href in seen or 'viber://' in href:
            continue
            
        full_url = urljoin(BASE_URL, href)
        if not full_url.startswith('http'):
             continue
             
        seen.add(href)
        urls.append(full_url)
            
    return urls

class RieltorParser:
    def __init__(self, html, url):
        self.html = html
        self.soup = BeautifulSoup(html, 'html.parser')
        self.url = url
        self.page_text = self.soup.get_text(" ", strip=True)
        self.title, self.address, self.rooms = self._parse_core()

    def _parse_core(self):
        addr = "Квартира"
        rooms = None
        
        # Try getting address from specific class first
        address_elem = self.soup.select_one('.offer-view-address, .address')
        if address_elem:
            addr = address_elem.get_text(", ", strip=True)
        else:
            address_m = re.search(r'Продаж квартири за адресою (.*?)(?:, Київ|,|\.)', self.page_text)
            if address_m:
                addr = address_m.group(1).strip()
            
        rooms_m = re.search(r'(\d+)\s*кімнат[аи]?', self.page_text)
        if rooms_m:
            rooms = int(rooms_m.group(1))
            
        title_rooms = f"{rooms}-кімнатна квартира" if rooms else "Квартира"
        title = f"{title_rooms}, {addr}"[:200]
        
        return title, addr, rooms

    def get_price_data(self):
        price = 0.0
        currency = "UAH"
        
        price_m = re.search(r'(\d[\d\s]*)\s*(?:\$|usd|грн|uah|€|eur)', self.page_text, re.IGNORECASE)
        if price_m:
            amount_str = price_m.group(1).replace(' ', '')
            curr_str = price_m.group(0).lower()
            try:
                price = float(amount_str)
            except ValueError:
                pass
                
            if '$' in curr_str or 'usd' in curr_str:
                currency = "USD"
            elif '€' in curr_str or 'eur' in curr_str:
                currency = "EUR"
                
        return price, currency

    def get_specs(self):
        area = None
        # Example: "85 / 30 / 20 м²" or "85 м²"
        area_m = re.search(r'(\d+(?:[\.,]\d+)?)\s*/\s*\d+\s*/\s*\d+\s*м²', self.page_text) 
        if not area_m:
            area_m = re.search(r'(\d+(?:[\.,]\d+)?)\s*м²', self.page_text)
            
        if area_m:
            try:
                area = float(area_m.group(1).replace(',', '.'))
            except ValueError:
                pass
                
        return self.rooms, area

    def get_location(self):
        city = None
        district = None
        region = None
        
        breadcrumbs = self.soup.select('.breadcrumbs li a, .breadcrumb li a')
        crumbs_text = [a.get_text(strip=True) for a in breadcrumbs]
        
        for crumb in crumbs_text:
            if "область" in crumb.lower():
                region = crumb
                continue
                
            if "р-н" in crumb.lower() or "район" in crumb.lower():
                if not district:
                    district = crumb
                continue
                
            normalized = normalize_city(crumb)
            if normalized and not city:
                city = normalized

        if not city:
            for word in self.address.split():
                normalized = normalize_city(word.replace(',', '').replace('.', ''))
                if normalized:
                    city = normalized
                    break

        address_parsed = AddressNormalizer.extract_from_text(self.address)
        if not address_parsed:
            address_parsed = self.address
            
        if city and address_parsed and city not in address_parsed:
            address_parsed = f"{city}, {address_parsed}"
        elif city and not address_parsed:
            address_parsed = city

        return address_parsed, city, district, region

    def get_images(self):
        seen = set()
        images = []
        
        img_tags = self.soup.select('.offer-view-gallery img, .gallery img, .slider img, img[data-src]')
        
        for img in img_tags:
            src = img.get('src') or img.get('data-src') or img.get('data-newsrc')
            if not src: 
                continue
            
            if any(skip in src.lower() for skip in ['icon', 'logo', 'avatar', 'banner', 'svg']):
                continue
                
            full_url = urljoin(self.url, src)
            if full_url not in seen:
                seen.add(full_url)
                images.append(full_url)
                
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
            "source_website": "rieltor_ua",
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
