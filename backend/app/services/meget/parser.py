import re
from urllib.parse import urljoin
from .config import GARBAGE_CLASSES, CITIES_UA
from .utils import clean_price_text, determine_currency, find_price_by_regex


class ListingParser:
    def __init__(self, soup, url):
        self.soup = soup
        self.url = url
        self._cleanup()
        self.page_text = self.soup.get_text(" ", strip=True)
        self.title = self._get_title()

    def _cleanup(self):
        for cls in GARBAGE_CLASSES:
            for tag in self.soup.find_all(class_=cls):
                tag.decompose()

    def _get_title(self):
        title_tag = self.soup.find('h1')
        return title_tag.text.strip() if title_tag else "No Title"

    def get_price_data(self):
        price = 0.0
        currency = "UAH"

        price_node = self.soup.find('span', id='price_uah')

        if not price_node:
            price = find_price_by_regex(self.page_text, r'(\d[\d\s]*)\s*грн')
            if price > 0:
                return price, "UAH"
        else:
            cleaned = clean_price_text(price_node.text)
            if cleaned:
                return float(cleaned), "UAH"

        return price, currency

    def get_specs(self):
        rooms = None
        area = None

        # Rooms
        rooms_match = re.search(r'(\d+)\s*[-]?\s*(?:ком|кім)', self.title, re.IGNORECASE)
        if rooms_match:
            rooms = int(rooms_match.group(1))

        # Area
        area_match = re.search(r'Площадь:.*?(\d+(?:[\.,]\d+)?)', self.page_text, re.IGNORECASE)
        if not area_match:
            area_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*м2', self.page_text)

        if area_match:
            area = float(area_match.group(1).replace(',', '.'))

        return rooms, area

    def get_location(self):
        city = None
        district = None
        address = self.title[:100]

        # Breadcrumbs Analysis
        breadcrumbs = self.soup.find('div', class_='breadcrumbs') or self.soup.find('ul', class_='breadcrumb')
        if breadcrumbs:
            crumbs = [a.text.strip() for a in breadcrumbs.find_all('a')]
            # Filter crumbs
            clean_crumbs = [c for c in crumbs if
                            c not in ['Главная', 'Продажа квартир', 'Продажа недвижимости', 'Meget', 'Недвижимость']]

            # Find City
            for crumb in clean_crumbs:
                norm = CITIES_UA.get(crumb, crumb)
                if norm in CITIES_UA.values():
                    city = norm
                    break

            # Find District
            if city:
                idx = -1
                for i, c in enumerate(clean_crumbs):
                    if CITIES_UA.get(c, c) == city:
                        idx = i;
                        break
                if idx != -1 and idx + 1 < len(clean_crumbs):
                    d_candidate = clean_crumbs[idx + 1]
                    if "р-н" in d_candidate or "район" in d_candidate.lower():
                        district = d_candidate

        # Fallback City Search in Title
        if not city:
            for k, v in CITIES_UA.items():
                if k in self.title:
                    city = v;
                    break

        # Build Address
        if city:
            city_regex = r'(' + city + r'|' + city[:-1] + r')'
            addr_match = re.search(f"{city_regex}" + r'[\s,]+(.*?)(?:рядом метро|Объявление|Оголошення|$)',
                                   self.page_text, re.IGNORECASE)

            if addr_match:
                raw_tail = addr_match.group(2).strip()
                for stop in ["Объявление", "Оголошення", "Продажа", "Цена", "Meget", "ЖК "]:
                    if stop in raw_tail: raw_tail = raw_tail.split(stop)[0]
                address = f"{city}, {raw_tail.strip().rstrip('.,')}"
            else:
                address = f"{city}"
                if district: address += f", {district}"

        return address, city, district

    def get_images(self):
        images = []
        # Main image
        main = self.soup.find('div', class_='image')
        if main and main.find('img'):
            src = main.find('img').get('src')
            if src: images.append(urljoin(self.url, src))

        # Gallery
        for t in self.soup.find_all('div', class_='small_image'):
            img = t.find('img')
            if img:
                src = img.get('src') or img.get('data-src')
                if src:
                    full_src = src.replace('s.jpg', '.jpg')
                    images.append(urljoin(self.url, full_src))
        return images

    def parse(self):
        price, currency = self.get_price_data()
        rooms, area = self.get_specs()
        address, city, district = self.get_location()
        images = self.get_images()

        return {
            "source_url": self.url,
            "source_website": "meget",
            "title": self.title,
            "price": price,
            "currency": currency,
            "address": address,
            "city": city,
            "district": district,
            "area": area,
            "rooms": rooms,
            "images": images
        }