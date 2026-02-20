
import pytest
from app.services.address_normalizer import AddressNormalizer

class TestAddressNormalizer:

    def test_basic_clean(self):
        assert AddressNormalizer._basic_clean("Київ, вул. Хрещатик, 1") == "Київ, вул. Хрещатик, 1"
        assert AddressNormalizer._basic_clean("м. Київ, вул #Хрещатик") == "м. Київ, вул Хрещатик"
        assert AddressNormalizer._basic_clean("Київ область") == "Київ"

    def test_translate_full_string(self):
        # Russian to Ukrainian
        assert AddressNormalizer._translate_full_string("улица Ленина") == "вулиця Соборна" # Note: Ленина -> вул. Соборна in dict
        assert AddressNormalizer._translate_full_string("Магнитогорская") == "Якова Гніздовського"
        assert AddressNormalizer._translate_full_string("площадь Победы") == "площа Победы" 

    def test_process_street_part(self):
        # Initial inversion
        assert AddressNormalizer._process_street_part("Шевченко Т.") == "Т. Шевченко"
        assert AddressNormalizer._process_street_part("Гончара О.") == "О. Гончара"
        # Translation
        assert AddressNormalizer._process_street_part("ул. Московская") == "вулиця Князів Острозьких"

    def test_normalize_simple(self):
        res = AddressNormalizer.normalize("Київ, вул. Хрещатик, 1")
        assert "Київ, вулиця Хрещатик, 1" in res or "Київ, вул. Хрещатик, 1" in res

    def test_normalize_renamed_street(self):
        res = AddressNormalizer.normalize("Київ, вул. Магнитогорская, 1а")
        # Should contain the new name
        assert any("Якова Гніздовського" in r for r in res)

    def test_extract_from_text(self):
        text = "Продам квартиру, вул. Хрещатик 25, центр."
        extracted = AddressNormalizer.extract_from_text(text)
        assert extracted == "вул. Хрещатик 25"

        text2 = "Чудова квартира на пр-т Перемоги 10/1"
        extracted2 = AddressNormalizer.extract_from_text(text2)
        assert extracted2 == "пр-т Перемоги 10/1"
