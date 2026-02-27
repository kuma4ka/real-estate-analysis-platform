import re

MIN_PRICE_USD = 2_000
MIN_TITLE_LENGTH = 15

MIN_PRICE_PER_SQM_USD = 100
MAX_PRICE_PER_SQM_USD = 50_000

SPAM_PATTERNS = [
    r'^test\b',
    r'^тест\b',
    r'\basdasd\b',
    r'\bqwerty\b',
    r'\blorem\s+ipsum\b',
    r'^xxx+$',
    r'^aaaa+$',
]

SPAM_REGEX = re.compile('|'.join(SPAM_PATTERNS), re.IGNORECASE)
class ListingValidator:
    @classmethod
    def validate(cls, data: dict) -> tuple[bool, str | None]:
        title = data.get('title', '')
        price = data.get('price', 0)
        area = data.get('area')

        if len(title) < MIN_TITLE_LENGTH:
            return False, f"Title too short ({len(title)} chars)"

        if SPAM_REGEX.search(title):
            return False, f"Spam detected in title: '{title[:50]}'"

        if not price or price <= 0:
            return False, "No price"

        if price < MIN_PRICE_USD:
            return False, f"Price too low: ${price}"

        if area and area > 0 and price > 0:
            price_per_sqm = price / area
            if price_per_sqm < MIN_PRICE_PER_SQM_USD:
                return False, f"Price/m² too low: ${price_per_sqm:.0f}/m² (min ${MIN_PRICE_PER_SQM_USD})"
            if price_per_sqm > MAX_PRICE_PER_SQM_USD:
                return False, f"Price/m² too high: ${price_per_sqm:.0f}/m² (max ${MAX_PRICE_PER_SQM_USD})"

        desc = data.get('description', '') or ''
        if len(desc) > 10 and SPAM_REGEX.search(desc):
            return False, "Spam detected in description"

        if area:
            if area < 8:
                return False, f"Area too small: {area} m²"
            if area > 500:
                return False, f"Area too large: {area} m²"

        return True, None
