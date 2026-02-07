import re

def clean_price_text(text):
    return re.sub(r'[^\d]', '', text)

def extract_number(text):
    clean = clean_price_text(text)
    return float(clean) if clean else 0.0

def determine_currency(text):
    text_lower = text.lower()
    if 'грн' in text_lower:
        return "UAH"
    if '$' in text_lower or 'у.е' in text_lower:
        return "USD"
    if '€' in text_lower:
        return "EUR"
    return "UAH"

def find_price_by_regex(text, pattern):
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return extract_number(match.group(1))
    return 0.0