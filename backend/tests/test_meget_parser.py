import pytest
from bs4 import BeautifulSoup
from unittest.mock import patch
from app.services.meget.parser import ListingParser

class TestListingParser:

    @pytest.fixture
    def mock_soup(self):
        html = """
        <html>
            <h1>Продам 2-к квартиру, вул. Київська 10</h1>
            <span id="price_uah">2 500 000 грн</span>
            <div class="address-sec">
                <h2><a href="#">м. Київ</a>, <a href="#">Печерський район</a></h2>
            </div>
            <div class="breadcrumbs">
                <ul>
                    <li><a href="#">Главная</a></li>
                    <li><a href="#">Київ</a></li>
                    <li><a href="#">Печерский р-н</a></li>
                </ul>
            </div>
            <div>Площадь: 50 м2</div>
            <div class="photo-gallery-area">
                <img src="/img1.jpg">
                <img data-src="/img2.jpg">
            </div>
        </html>
        """
        return BeautifulSoup(html, 'html.parser')

    @patch('app.services.ai_address_parser.AIAddressParser.parse')
    def test_parse_basics(self, mock_ai_parse, mock_soup):
        # Mock the AI parser returning None, so we test the heuristic logic
        mock_ai_parse.return_value = None
        
        parser = ListingParser(mock_soup, "http://example.com/listing/1")
        data = parser.parse()

        assert data['title'] == "Продам 2-к квартиру, вул. Київська 10"
        assert data['price'] == 2500000.0
        assert data['currency'] == "UAH"
        assert data['city'] == "Київ"
        assert data['district'] in ["Печерський район", "Печерский р-н", "Печерський р-н"]
        assert data['area'] == 50.0
        assert data['rooms'] == 2
        assert len(data['images']) == 2
        assert "http://example.com/img1.jpg" in data['images']
        
    @patch('app.services.ai_address_parser.AIAddressParser.parse')
    def test_ai_fallback_is_used(self, mock_ai_parse, mock_soup):
        # Mock the AI parser returning a valid structured result
        mock_ai_parse.return_value = {
            'city': 'Київ',
            'street': 'вулиця Тестова',
            'number': '42А',
            'district': 'Солом\'янський',
            'region': 'Київська_mock'
        }
        
        parser = ListingParser(mock_soup, "http://example.com/listing/2")
        data = parser.parse()
        
        assert data['address'] == "Київ, вулиця Тестова, 42А"
        assert data['city'] == "Київ"
        assert data['district'] == "Солом\'янський"
        assert data['region'] == "Київська_mock"
