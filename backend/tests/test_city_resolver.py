from app.api.properties import _resolve_city_alias
from app.services.address_normalizer import AddressNormalizer


class TestCityResolver:
    def test_resolve_city_alias_kyiv_lower(self):
        assert _resolve_city_alias("kyiv") == "Київ"

    def test_resolve_city_alias_kyiv_cyrillic(self):
        assert _resolve_city_alias("Київ") == "Київ"

    def test_resolve_city_alias_unknown(self):
        assert _resolve_city_alias("Невідоме") == "Невідоме"

    def test_resolve_city_alias_kharkiv(self):
        assert _resolve_city_alias("kharkiv") == "Харків"

    def test_resolve_city_alias_odesa(self):
        assert _resolve_city_alias("odesa") == "Одеса"


class TestAddressNormalizerIntegration:
    def test_normalize_returns_non_empty_list(self):
        result = AddressNormalizer.normalize("Вул. Незалежності 1")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_normalize_whitespace_trimmed(self):
        result = AddressNormalizer.normalize("  Вул. Незалежності 1  ")
        assert isinstance(result, list)
        for r in result:
            assert r == r.strip()
