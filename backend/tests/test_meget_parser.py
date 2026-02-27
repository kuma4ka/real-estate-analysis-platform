import pytest
from bs4 import BeautifulSoup
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

    def test_parse_basics(self, mock_soup):
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

    def test_address_extracted_from_title(self, mock_soup):
        """Parser should extract street address via AddressNormalizer when breadcrumbs
        do not contain a recognisable street name."""
        parser = ListingParser(mock_soup, "http://example.com/listing/2")
        data = parser.parse()

        # AddressNormalizer should pull the street from the h1 title
        assert data['address'] is not None
        assert data['city'] == "Київ"
