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
        address = None

        # 0. Primary Source: <address class="address-sec"> (Most reliable for full address)
        address_sec = self.soup.find('address', class_='address-sec')
        if address_sec:
            h2 = address_sec.find('h2') or address_sec.find('h1') or address_sec.find(class_='detail-page-topic')
            if h2:
                # City is often in <a> tag
                city_link = h2.find('a')
                if city_link:
                    city_text = city_link.text.strip()
                    # Validate city against config
                    norm = CITIES_UA.get(city_text, city_text)
                    if norm in CITIES_UA.values():
                        city = norm
                    else:
                        city = city_text # Trust the link text even if not in config
                
                # Address text is the full text of h2
                full_text = h2.get_text(" ", strip=True)
                # Clean up multiple spaces and formatting
                address = re.sub(r'\s+', ' ', full_text)
                address = re.sub(r'\s+,\s*', ', ', address)

        # 1. Breadcrumbs Analysis (Secondary source for City/District if parsing failed to get them)
        if not city or not district:
            breadcrumbs = self.soup.find('div', class_='breadcrumbs') or self.soup.find('ul', class_='breadcrumb')
            if breadcrumbs:
                crumbs = [a.text.strip() for a in breadcrumbs.find_all('a')]
                clean_crumbs = [c for c in crumbs if
                                c not in ['Главная', 'Продажа квартир', 'Продажа недвижимости', 'Meget', 'Недвижимость']]

                for i, crumb in enumerate(clean_crumbs):
                    norm = CITIES_UA.get(crumb, crumb)
                    if norm in CITIES_UA.values():
                        if not city: city = norm
                        # Potential district follows city
                        if i + 1 < len(clean_crumbs):
                            d_candidate = clean_crumbs[i + 1]
                            if "р-н" in d_candidate or "район" in d_candidate.lower():
                                district = d_candidate
                        break
        
        # Fallback City (Last resort)
        if not city:
            # Check title first
            for k, v in CITIES_UA.items():
                if k in self.title:
                    city = v;
                    break
            # Only default to Kyiv if we have ABSOLUTELY no clue and it's kiev.ua
            # But be careful, Meget has subdomain specific cookies or logic, but URL is often mege.kiev.ua for all.
            # Let's REMOVE the hard default to Kyiv unless title text strongly implies it or we are desperate.
            # Better to have None than wrong city.
            if not city and "kiev.ua" in self.url and "Киев" in self.title:
                 city = "Київ"


        # 2. Address Logic (Fallback if address-sec method failed)
        if not address:
            title_text = self.title
            
            # Extended prefixes to strip (including room counts like "1-ком.")
            prefixes = [
                r'Продажа.*?квартиры', r'Продам.*?квартиру', r'Объявление №\d+ - ',
                r'\d+\s*-?\s*ком\.?', r'\d+\s*-?\s*к\.', r'без комиссии'
            ]
            
            cleaned_title = title_text
            for p in prefixes:
                cleaned_title = re.sub(p, '', cleaned_title, flags=re.IGNORECASE).strip()
                
            # Clean leading/trailing punctuation
            cleaned_title = cleaned_title.strip(" .,-")

            # Validation: Does it look like an address?
            if len(cleaned_title) > 4 and cleaned_title.lower() != title_text.lower():
                 # Check if it contains street markers
                 street_markers = [
                     'ул.', 'вул.', 'просп.', 'пров.', 'бульв.', 'майдан', 'наб.', 'шосе', 
                     'узвіз', 'тупик', 'площа', 'квартал', 'алея', 'проспект', 'улица', 'переулок'
                 ]
                 if any(m in cleaned_title.lower() for m in street_markers):
                     address = cleaned_title
                 else:
                     if not re.match(r'^\d+[\s-]*ком\.?$', cleaned_title, re.IGNORECASE):
                         address = cleaned_title

            # If title extraction failed, try breadcrumbs composition
            if not address:
                 parts = []
                 if city: parts.append(city)
                 if district: parts.append(district)
                 address = ", ".join(parts) if parts else None

        # Final Polish: Ensure city is in address for geocoder context
        # If address was from address-sec, it likely includes city.
        if city and address and city not in address:
            address = f"{city}, {address}"
        elif city and not address:
            address = city 

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