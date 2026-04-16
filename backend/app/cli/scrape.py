import time
import click
from flask.cli import with_appcontext

from app.services.meget import scrape_meget_listing, get_listing_urls as meget_get_listing_urls
from app.services.bon_ua import scrape_bon_ua_listing, get_listing_urls as bon_ua_get_listing_urls
from app.cli.geocode import _execute_scraping


@click.command(name='scrape_meget')
@click.option('--workers', default=5, help='Number of parallel threads')
@click.option('--pages', default=1, help='Number of pages to scrape from global catalog')
@with_appcontext
def scrape_meget_command(workers, pages):
    from app.models import Source
    source = Source.query.filter_by(name='MEGET').first()
    if not source or not source.is_active:
        print("MEGET source is disabled or missing.")
        return

    print(f"🚀 Starting Meget scraping with {workers} threads, {pages} pages from {source.base_url}...")

    all_target_urls = set()
    for page in range(1, pages + 1):
        print(f"[CRAWLER] Page {page}...")
        urls = meget_get_listing_urls(base_url=source.base_url, page=page)
        if urls:
            all_target_urls.update(urls)
        time.sleep(1)

    _execute_scraping(list(all_target_urls), workers, scrape_meget_listing)


@click.command(name='scrape_bon_ua')
@click.option('--workers', default=5, help='Number of parallel threads')
@click.option('--pages', default=1, help='Number of pages to scrape from global catalog')
@with_appcontext
def scrape_bon_ua_command(workers, pages):
    from app.models import Source
    source = Source.query.filter_by(name='BON.UA').first()
    if not source or not source.is_active:
        print("BON.UA source is disabled or missing.")
        return

    print(f"🚀 Starting Bon.ua scraping with {workers} threads, {pages} pages from {source.base_url}...")

    all_target_urls = set()
    for page in range(1, pages + 1):
        print(f"[CRAWLER] Page {page}...")
        urls = bon_ua_get_listing_urls(listings_url=source.base_url, page=page)
        if urls:
            all_target_urls.update(urls)
        time.sleep(1)

    _execute_scraping(list(all_target_urls), workers, scrape_bon_ua_listing)
