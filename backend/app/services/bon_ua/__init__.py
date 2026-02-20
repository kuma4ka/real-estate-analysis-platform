from .network import fetch_html
from .parser import BonUaParser, get_listing_urls

def scrape_bon_ua_listing(url):
    html = fetch_html(url)
    if not html:
        return None
    parser = BonUaParser(html, url)
    return parser.parse()

__all__ = ['fetch_html', 'BonUaParser', 'get_listing_urls', 'scrape_bon_ua_listing']
