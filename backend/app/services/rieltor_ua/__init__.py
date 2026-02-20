from .network import fetch_html
from .parser import RieltorParser, get_listing_urls

def scrape_rieltor_ua_listing(url):
    html = fetch_html(url)
    if not html:
        return None
    parser = RieltorParser(html, url)
    return parser.parse()

__all__ = ['fetch_html', 'RieltorParser', 'get_listing_urls', 'scrape_rieltor_ua_listing']
