import pytest
from app.api.properties import _resolve_city_alias
from app.services.address_normalizer import AddressNormalizer

class TestCityResolver:
    def test_resolve_city_alias_kyiv_lower(self):
        assert _resolve_city_alias("kyiv") == "Київ"

    def test_resolve_city_alias_kyiv_cyrillic(self):
        assert _resolve_city_alias("Київ") == "Київ"

    def test_resolve_city_alias_unknown(self):
        assert _resolve_city_alias("Невідоме") == "Невідоме"

    def test_normalize_address_trim(self):
        # In the practical work it states normalize_address " Вул. Незалежності 1 " -> "Вул. Незалежності 1"
        # The AddressNormalizer returns a list, so we check the first element
        result = AddressNormalizer.normalize(" Вул. Незалежності 1 ")
        assert result[0] == "Вул. Незалежності 1"
