import pytest
from bs4 import BeautifulSoup
from app.services.meget.parser import ListingParser


BASE_HTML = """
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


class TestListingParser:

    @pytest.fixture
    def mock_soup(self):
        return BeautifulSoup(BASE_HTML, 'html.parser')

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
        parser = ListingParser(mock_soup, "http://example.com/listing/2")
        data = parser.parse()

        assert data['address'] is not None
        assert data['city'] == "Київ"

    def test_parse_without_price_tag(self):
        html_no_price = BASE_HTML.replace('<span id="price_uah">2 500 000 грн</span>', '')
        soup = BeautifulSoup(html_no_price, 'html.parser')
        parser = ListingParser(soup, "http://example.com/listing/3")
        data = parser.parse()
        assert data['price'] == 0.0 or data['price'] is None

    def test_parse_without_images(self):
        html_no_img = BASE_HTML.replace('<div class="photo-gallery-area">', '').replace(
            '<img src="/img1.jpg">', '').replace('<img data-src="/img2.jpg">', '').replace('</div>', '', 1)
        soup = BeautifulSoup(html_no_img, 'html.parser')
        parser = ListingParser(soup, "http://example.com/listing/4")
        data = parser.parse()
        assert isinstance(data['images'], list)

    def test_parse_source_url_preserved(self, mock_soup):
        url = "http://example.com/listing/99"
        parser = ListingParser(mock_soup, url)
        data = parser.parse()
        assert data['source_url'] == url
