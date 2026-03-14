from app.services.cities import normalize_city, get_center, get_region_center


class TestNormalizeCity:
    def test_canonical_name_unchanged(self):
        assert normalize_city("Київ") == "Київ"
        assert normalize_city("Харків") == "Харків"

    def test_english_alias(self):
        assert normalize_city("Kyiv") == "Київ"
        assert normalize_city("Kharkiv") == "Харків"
        assert normalize_city("Lviv") == "Львів"
        assert normalize_city("Odesa") == "Одеса"
        assert normalize_city("Dnipro") == "Дніпро"

    def test_old_russian_alias(self):
        assert normalize_city("Киев") == "Київ"
        assert normalize_city("Харьков") == "Харків"
        assert normalize_city("Одесса") == "Одеса"
        assert normalize_city("Днепр") == "Дніпро"
        assert normalize_city("Днепропетровск") == "Дніпро"

    def test_case_insensitive(self):
        assert normalize_city("kyiv") == "Київ"
        assert normalize_city("KYIV") == "Київ"
        assert normalize_city("kYiV") == "Київ"

    def test_unknown_city_returns_none(self):
        assert normalize_city("Atlantis") is None
        assert normalize_city("") is None
        assert normalize_city(None) is None

    def test_whitespace_stripped(self):
        assert normalize_city("  Київ  ") == "Київ"


class TestGetCenter:
    def test_known_city_returns_coordinates(self):
        result = get_center("Київ")
        assert result is not None
        lat, lng = result
        assert isinstance(lat, float)
        assert isinstance(lng, float)
        assert 49 < lat < 51
        assert 29 < lng < 32

    def test_english_alias_resolves(self):
        result = get_center("Kyiv")
        assert result is not None

    def test_unknown_city_returns_none(self):
        assert get_center("Nonexistent") is None
        assert get_center("") is None
        assert get_center(None) is None


class TestGetRegionCenter:
    def test_region_with_oblast_suffix(self):
        result = get_region_center("Київська область")
        assert result is not None
        center, city = result
        assert city == "Київ"

    def test_region_without_oblast_suffix(self):
        result = get_region_center("Київська")
        assert result is not None
        _, city = result
        assert city == "Київ"

    def test_none_input(self):
        assert get_region_center(None) is None
        assert get_region_center("") is None
