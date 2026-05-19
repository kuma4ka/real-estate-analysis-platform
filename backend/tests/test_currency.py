import pytest
from unittest.mock import patch
from app.services.currency import convert_to_usd, get_nbu_rates


MOCK_RATES = {'USD': 40.0, 'EUR': 44.0}


class TestConvertToUsd:
    def test_usd_is_returned_as_is(self):
        assert convert_to_usd(1000.0, 'USD') == 1000.0

    def test_uah_to_usd(self):
        with patch('app.services.currency.get_nbu_rates', return_value=MOCK_RATES):
            assert convert_to_usd(40.0, 'UAH') == pytest.approx(1.0)

    def test_eur_to_usd(self):
        with patch('app.services.currency.get_nbu_rates', return_value=MOCK_RATES):
            result = convert_to_usd(1.0, 'EUR')
            assert result == pytest.approx(1.1)

    def test_zero_price_returns_zero(self):
        assert convert_to_usd(0.0, 'USD') == 0.0

    def test_negative_price_returns_zero(self):
        assert convert_to_usd(-100.0, 'USD') == 0.0

    def test_case_insensitive_currency(self):
        with patch('app.services.currency.get_nbu_rates', return_value=MOCK_RATES):
            assert convert_to_usd(40.0, 'uah') == pytest.approx(1.0)
            assert convert_to_usd(1000.0, 'usd') == 1000.0

    def test_unknown_currency_falls_back_to_uah(self):
        with patch('app.services.currency.get_nbu_rates', return_value=MOCK_RATES):
            result = convert_to_usd(40.0, 'GBP')
            assert result == pytest.approx(1.0)

    def test_large_price_converts_correctly(self):
        with patch('app.services.currency.get_nbu_rates', return_value=MOCK_RATES):
            result = convert_to_usd(4_000_000.0, 'UAH')
            assert result == pytest.approx(100_000.0)


class TestGetNbuRatesFallback:
    def test_fallback_on_request_error(self):
        from app import create_app
        app = create_app()
        with patch('app.services.currency.requests.get', side_effect=Exception("network error")):
            with app.app_context():
                from app import cache
                cache.delete('nbu_rates')
                rates = get_nbu_rates()
                assert 'USD' in rates
                assert rates['USD'] > 0

    def test_fallback_values_are_positive(self):
        from app import create_app
        app = create_app()
        with patch('app.services.currency.requests.get', side_effect=Exception("fail")):
            with app.app_context():
                from app import cache
                cache.delete('nbu_rates')
                rates = get_nbu_rates()
                assert rates['USD'] > 0
                assert rates['EUR'] > 0
