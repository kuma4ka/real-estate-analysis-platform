from .network import get_listing_urls, fetch_html
from .parser import ListingParser

def scrape_meget_listing(url):
    soup = fetch_html(url)
    if not soup:
        return None

    parser = ListingParser(soup, url)
    return parser.parse()

__all__ = ['get_listing_urls', 'fetch_html', 'ListingParser', 'scrape_meget_listing']