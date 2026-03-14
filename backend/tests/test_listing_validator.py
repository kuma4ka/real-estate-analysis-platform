from app.services.listing_validator import ListingValidator


VALID_LISTING = {
    'title': 'Продам 2-кімнатну квартиру у Київ',
    'price': 50_000,
    'area': 60.0,
    'description': 'Гарна квартира з ремонтом в центрі',
}


class TestListingValidatorValid:
    def test_valid_listing_passes(self):
        ok, reason = ListingValidator.validate(VALID_LISTING)
        assert ok is True
        assert reason is None

    def test_no_area_is_allowed(self):
        data = {**VALID_LISTING, 'area': None}
        ok, _ = ListingValidator.validate(data)
        assert ok is True


class TestListingValidatorTitle:
    def test_title_too_short(self):
        data = {**VALID_LISTING, 'title': 'Short'}
        ok, reason = ListingValidator.validate(data)
        assert ok is False
        assert 'short' in reason.lower()

    def test_title_spam_test(self):
        data = {**VALID_LISTING, 'title': 'test listing in Kyiv center'}
        ok, reason = ListingValidator.validate(data)
        assert ok is False
        assert 'spam' in reason.lower()

    def test_title_spam_lorem(self):
        data = {**VALID_LISTING, 'title': 'Lorem ipsum dolor sit amet'}
        ok, reason = ListingValidator.validate(data)
        assert ok is False

    def test_title_spam_qwerty(self):
        data = {**VALID_LISTING, 'title': 'qwerty test listing in Kyiv'}
        ok, reason = ListingValidator.validate(data)
        assert ok is False


class TestListingValidatorPrice:
    def test_price_zero(self):
        data = {**VALID_LISTING, 'price': 0}
        ok, reason = ListingValidator.validate(data)
        assert ok is False
        assert 'price' in reason.lower()

    def test_price_negative(self):
        data = {**VALID_LISTING, 'price': -100}
        ok, reason = ListingValidator.validate(data)
        assert ok is False

    def test_price_too_low(self):
        data = {**VALID_LISTING, 'price': 500}
        ok, reason = ListingValidator.validate(data)
        assert ok is False
        assert 'low' in reason.lower()

    def test_price_missing(self):
        data = {k: v for k, v in VALID_LISTING.items() if k != 'price'}
        ok, reason = ListingValidator.validate(data)
        assert ok is False


class TestListingValidatorPricePerSqm:
    def test_price_per_sqm_too_low(self):
        # 3000 USD / 60 m² = 50 USD/m² < 100 minimum
        data = {**VALID_LISTING, 'price': 3_000, 'area': 60.0}
        ok, reason = ListingValidator.validate(data)
        assert ok is False
        assert 'low' in reason.lower()

    def test_price_per_sqm_too_high(self):
        # 5_000_000 USD / 10 m² = 500,000 USD/m² > 50,000 maximum
        data = {**VALID_LISTING, 'price': 5_000_000, 'area': 10.0}
        ok, reason = ListingValidator.validate(data)
        assert ok is False
        assert 'high' in reason.lower()


class TestListingValidatorArea:
    def test_area_too_small(self):
        data = {**VALID_LISTING, 'area': 5.0}
        ok, reason = ListingValidator.validate(data)
        assert ok is False
        assert 'small' in reason.lower()

    def test_area_too_large(self):
        # 600 m² exceeds max area of 500; price chosen to give valid price/sqm
        data = {**VALID_LISTING, 'area': 600.0, 'price': 12_000_000}
        ok, reason = ListingValidator.validate(data)
        assert ok is False
        assert 'large' in reason.lower()
