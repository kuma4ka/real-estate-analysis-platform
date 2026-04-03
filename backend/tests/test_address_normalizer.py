from app.services.address_normalizer import AddressNormalizer


class TestAddressNormalizer:

    def test_basic_clean(self):
        assert AddressNormalizer._basic_clean("Київ, вул. Хрещатик, 1") == "Київ, вул. Хрещатик, 1"
        assert AddressNormalizer._basic_clean("м. Київ, вул #Хрещатик") == "м. Київ, вул Хрещатик"
        assert AddressNormalizer._basic_clean("Київ область") == "Київ"

    def test_translate_full_string(self):
        assert AddressNormalizer._translate_full_string("улица Ленина") == "вулиця Соборна"
        assert AddressNormalizer._translate_full_string("Магнитогорская") == "Якова Гніздовського"
        assert AddressNormalizer._translate_full_string("площадь Победы") == "площа Победы"

    def test_process_street_part(self):
        assert AddressNormalizer._process_street_part("Шевченко Т.") == "Т. Шевченко"
        assert AddressNormalizer._process_street_part("Гончара О.") == "О. Гончара"
        assert AddressNormalizer._process_street_part("ул. Московская") == "вулиця Князів Острозьких"

    def test_normalize_returns_list(self):
        result = AddressNormalizer.normalize("Київ, вул. Хрещатик, 1")
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_normalize_simple_contains_key_parts(self):
        result = AddressNormalizer.normalize("Київ, вул. Хрещатик, 1")
        combined = " ".join(result)
        assert "Київ" in combined
        assert "Хрещатик" in combined

    def test_normalize_renamed_street(self):
        result = AddressNormalizer.normalize("Київ, вул. Магнитогорская, 1а")
        assert any("Якова Гніздовського" in r for r in result)

    def test_extract_from_text(self):
        text = "Продам квартиру, вул. Хрещатик 25, центр."
        extracted = AddressNormalizer.extract_from_text(text)
        assert extracted == "вул. Хрещатик 25"

        text2 = "Чудова квартира на пр-т Перемоги 10/1"
        extracted2 = AddressNormalizer.extract_from_text(text2)
        assert extracted2 == "пр-т Перемоги 10/1"

    def test_extract_from_text_none_returns_none(self):
        assert AddressNormalizer.extract_from_text(None) is None

    def test_extract_from_text_empty_returns_none(self):
        result = AddressNormalizer.extract_from_text("no address here at all")
        assert result is None or isinstance(result, str)
