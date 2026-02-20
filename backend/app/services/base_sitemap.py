import xml.etree.ElementTree as ET
from urllib.parse import urlparse

class BaseSitemapFetcher:
    def __init__(self, fetch_func):
        self.fetch = fetch_func
        
    def _parse_xml(self, xml_content):
        """Extract all URLs from a standard sitemap.xml"""
        try:
            root = ET.fromstring(xml_content)
            # Handle XML namespaces usually present in sitemaps
            urls = []
            for child in root:
                for subchild in child:
                    if 'loc' in subchild.tag:
                        urls.append(subchild.text)
            return urls
        except Exception as e:
            print(f"Error parsing XML: {e}")
            return []

    def get_listing_urls(self, sitemap_url, filter_url_pattern=None):
        """
        Fetch a sitemap, extract URLs, and optionally filter them.
        Handles both sitemap indexes (recursively) and standard urlsets.
        """
        print(f"Fetching sitemap: {sitemap_url}")
        content = self.fetch(sitemap_url)
        if not content:
            return []
            
        urls = self._parse_xml(content)
        
        # Check if this is a sitemap index (ends with .xml but contains other sitemaps)
        if urls and urls[0].endswith('.xml'):
            print(f"Detected sitemap index with {len(urls)} sub-sitemaps.")
            all_leaf_urls = []
            for sub_sitemap in urls:
                all_leaf_urls.extend(self.get_listing_urls(sub_sitemap, filter_url_pattern))
            return all_leaf_urls
            
        # Standard URL set
        if filter_url_pattern:
            urls = [u for u in urls if filter_url_pattern in u]
            
        print(f"Found {len(urls)} valid URLs in {sitemap_url}")
        return urls
