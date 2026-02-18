import re
from urllib.parse import urljoin
from .config import GARBAGE_CLASSES
from .utils import clean_price_text, find_price_by_regex
from app.services.cities import normalize_city
from app.services.address_normalizer import AddressNormalizer


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

        rooms_match = re.search(r'(\d+)\s*[-]?\s*(?:ком|кім)', self.title, re.IGNORECASE)
        if rooms_match:
            rooms = int(rooms_match.group(1))

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
        region = None

        address_sec = self.soup.find('address', class_='address-sec')
        if address_sec:
            h2 = address_sec.find('h2') or address_sec.find('h1') or address_sec.find(class_='detail-page-topic')
            if h2:
                for link in h2.find_all('a'):
                    link_text = link.text.strip()
                    if not link_text:
                        continue
                    if 'область' in link_text.lower():
                        if not region:
                            region = link_text
                        continue
                    if 'р-н' in link_text or 'район' in link_text.lower():
                        if not district:
                            district = link_text
                        continue
                    city = normalize_city(link_text) or link_text

                full_text = h2.get_text(" ", strip=True)
                address = re.sub(r'\s+', ' ', full_text)
                address = re.sub(r'\s+,\s*', ', ', address)

                # Fallback: parse plain text when no <a> links found
                if not city and not region:
                    text_parts = [p.strip() for p in address.split(',') if p.strip()]
                    remaining = []
                    for part in text_parts:
                        if 'область' in part.lower():
                            region = part
                        elif 'р-н' in part.lower() or 'район' in part.lower():
                            district = part
                        else:
                            remaining.append(part)
                    if remaining:
                        city = normalize_city(remaining[0]) or remaining[0]
                        address = ', '.join(remaining)
                    else:
                        address = ', '.join(text_parts)

                # Strip region/district from address text
                addr_parts = [p.strip() for p in address.split(',') if p.strip()]
                addr_parts = [
                    p for p in addr_parts
                    if 'область' not in p.lower() and 'р-н' not in p.lower()
                ]
                # Deduplicate consecutive city names
                if len(addr_parts) >= 2 and normalize_city(addr_parts[0]) and normalize_city(addr_parts[0]) == normalize_city(addr_parts[1]):
                    addr_parts = addr_parts[1:]
                address = ', '.join(addr_parts)

        # Breadcrumbs
        breadcrumbs = self.soup.find('div', class_='breadcrumbs') or self.soup.find('ul', class_='breadcrumb')
        if breadcrumbs:
            crumbs = [a.text.strip() for a in breadcrumbs.find_all('a')]
            skip = {'Главная', 'Продажа квартир', 'Продажа недвижимости', 'Meget', 'Недвижимость'}
            clean_crumbs = [c for c in crumbs if c not in skip]

            for i, crumb in enumerate(clean_crumbs):
                if "область" in crumb.lower():
                    region = crumb
                    continue

                normalized = normalize_city(crumb)
                if normalized:
                    if not city:
                        city = normalized
                    if i + 1 < len(clean_crumbs):
                        d_candidate = clean_crumbs[i + 1]
                        if "р-н" in d_candidate or "район" in d_candidate.lower():
                            district = d_candidate

                if "р-н" in crumb or "район" in crumb.lower():
                    if not district:
                        district = crumb

        # Fallback: city from title
        if not city:
            for word in self.title.split():
                normalized = normalize_city(word.strip('.,'))
                if normalized:
                    city = normalized
                    break

        # AI parsing
        from app.services.ai_address_parser import AIAddressParser

        breadcrumbs_text = " > ".join([a.text.strip() for a in breadcrumbs.find_all('a')]) if breadcrumbs else ""

        ai_result = AIAddressParser.parse(
            title=self.title,
            description=self.page_text,
            breadcrumbs_text=breadcrumbs_text
        )

        if ai_result and ai_result.get('city'):
            city = ai_result.get('city')
            region = ai_result.get('region') or region
            district = ai_result.get('district') or district

            parts = []
            if ai_result.get('street'):
                parts.append(ai_result['street'])
            if ai_result.get('number'):
                parts.append(ai_result['number'])

            address = ", ".join(parts) if parts else city

            if city not in address:
                address = f"{city}, {address}"

        elif not address:
            cleaned_title = re.sub(r'(Продажа|Продам).*?(квартиры|квартиру)', '', self.title, flags=re.IGNORECASE)
            cleaned_title = re.sub(r'Объявление №\d+', '', cleaned_title)

            extracted = AddressNormalizer.extract_from_text(cleaned_title)
            if not extracted:
                extracted = AddressNormalizer.extract_from_text(self.page_text)
            if extracted:
                address = extracted

        # Ensure city is in address
        if city and address:
            has_city = city in address
            if not has_city:
                from app.services.cities import CITIES
                city_info = CITIES.get(city)
                if city_info:
                    has_city = any(alias in address for alias in city_info['aliases'])
            if not has_city:
                address = f"{city}, {address}"
        elif city and not address:
            address = city

        return address, city, district, region

    def get_images(self):
        images = []
        main = self.soup.find('div', class_='image')
        if main and main.find('img'):
            src = main.find('img').get('src')
            if src:
                images.append(urljoin(self.url, src))

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
        address, city, district, region = self.get_location()
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
            "region": region,
            "area": area,
            "rooms": rooms,
            "images": images
        }