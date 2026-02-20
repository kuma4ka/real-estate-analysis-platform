from app.services.meget.utils import clean_price_text, extract_number, find_price_by_regex

def test_clean_price_text():
    assert clean_price_text("2 500 000 грн") == "2500000"
    assert clean_price_text("10.50$") == "1050"
    assert clean_price_text("Без цены") == ""

def test_extract_number():
    assert extract_number("2 500 000 грн") == 2500000.0
    assert extract_number("Без цены") == 0.0

def test_find_price_by_regex():
    text = "Цена: 1 200 500 грн за объект."
    pattern = r'Цена:\s*([\d\s]+)\s*грн'
    
    assert find_price_by_regex(text, pattern) == 1200500.0
    assert find_price_by_regex("Нет цены", pattern) == 0.0
