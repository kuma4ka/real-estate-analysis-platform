import click
import time
import random
from datetime import datetime
from flask.cli import with_appcontext
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import Property
from app.services.scraper import scrape_meget_listing, get_listing_urls


@click.command(name='scrape_meget')
@with_appcontext
def scrape_command():
    print("[INFO] Starting scraping job for Meget...")

    urls = get_listing_urls()

    if not urls:
        print("[WARNING] No URLs found or connection failed.")
        return

    print(f"[INFO] Found {len(urls)} listings. Processing...")

    stats = {
        'new': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }

    for url in urls:
        time.sleep(random.uniform(1.0, 2.0))

        data = scrape_meget_listing(url)

        if not data:
            print(f"[ERROR] Failed to scrape URL: {url}")
            stats['errors'] += 1
            continue

        try:
            existing_prop = Property.query.filter_by(source_url=url).first()

            if existing_prop:
                if existing_prop.price != data['price']:
                    old_price = existing_prop.price

                    existing_prop.price = data['price']
                    existing_prop.currency = data['currency']
                    existing_prop.updated_at = datetime.utcnow()

                    db.session.commit()
                    stats['updated'] += 1
                    print(f"[UPDATED] ID {existing_prop.id}: Price changed {old_price} -> {data['price']}")
                else:
                    stats['skipped'] += 1
            else:
                new_prop = Property(
                    title=data['title'],
                    source_url=data['source_url'],
                    source_website='meget',
                    price=data.get('price'),
                    currency=data.get('currency'),
                    address=data.get('address'),
                    area=data.get('area'),
                    rooms=data.get('rooms'),
                    description=f"Scraped from {data['source_website']}"
                )
                db.session.add(new_prop)
                db.session.commit()
                stats['new'] += 1
                print(f"[CREATED] New listing: {data['title'][:50]}... (${data['price']})")

        except IntegrityError:
            db.session.rollback()
            print(f"[ERROR] Integrity error (duplicate) for URL: {url}")
            stats['errors'] += 1
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Database error: {str(e)}")
            stats['errors'] += 1

    print("-" * 40)
    print(f"[INFO] Job finished.")
    print(
        f"Stats: New: {stats['new']} | Updated: {stats['updated']} | Skipped: {stats['skipped']} | Errors: {stats['errors']}")