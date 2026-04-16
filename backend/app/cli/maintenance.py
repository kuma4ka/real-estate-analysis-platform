import time
import click
from flask.cli import with_appcontext

from app import db
from app.models import Property
from app.cli.geocode import get_lat_long, _execute_scraping
from app.services.bon_ua import scrape_bon_ua_listing


@click.command(name='regeocode_all')
@with_appcontext
def regeocode_all_command():
    props = Property.query.filter(Property.address.isnot(None)).all()
    print(f"Re-geocoding {len(props)} properties...")

    count = 0
    for p in props:
        lat, lng, canonical, precision = get_lat_long(p.address)
        if lat and lng:
            p.latitude = lat
            p.longitude = lng
            p.geocode_precision = precision
            if canonical:
                p.address = canonical
            count += 1
            if count % 10 == 0:
                db.session.commit()
                print(f"Updated {count}")
                time.sleep(1)
        else:
            p.latitude = None
            p.longitude = None
            p.geocode_precision = None

    db.session.commit()
    print(f"Done. Updated {count}/{len(props)}.")


@click.command(name='regeocode_ids')
@click.argument('ids_str')
@with_appcontext
def regeocode_ids_command(ids_str):
    ids = [int(i.strip()) for i in ids_str.split(',')]
    print(f"Re-geocoding {len(ids)} properties: {ids}")

    props = Property.query.filter(Property.id.in_(ids)).all()

    for p in props:
        print(f"#{p.id}: {p.address}")
        lat, lng, canonical, precision = get_lat_long(p.address)
        if lat and lng:
            print(f"  ✅ {lat}, {lng} ({precision})")
            p.latitude = lat
            p.longitude = lng
            p.geocode_precision = precision
            if canonical:
                p.address = canonical
        else:
            print("  ❌ Failed")
            p.latitude = None
            p.longitude = None
            p.geocode_precision = None

    db.session.commit()
    print("Done.")


@click.command('backfill-images')
@click.option('--limit', default=0, help='Max properties to process (0 = all)')
@with_appcontext
def backfill_images(limit):
    """Re-fetch images for properties that have none."""
    from app.services.meget import fetch_html
    from app.services.meget.parser import ListingParser

    query = Property.query.filter(
        db.or_(Property.images.is_(None), Property.images == '[]')
    ).filter(Property.source_url.isnot(None))

    if limit > 0:
        query = query.limit(limit)

    props = query.all()
    print(f"Found {len(props)} properties without images.")

    updated = 0
    for i, p in enumerate(props, 1):
        print(f"[{i}/{len(props)}] #{p.id}: {p.source_url}")
        soup = fetch_html(p.source_url)
        if not soup:
            print("  ⚠ Could not fetch page")
            time.sleep(1)
            continue

        parser = ListingParser(soup, p.source_url)
        images = parser.get_images()

        if images:
            p.images = images
            updated += 1
            print(f"  ✅ Found {len(images)} images")
        else:
            print("  ❌ No images found")

        if i % 25 == 0:
            db.session.commit()

        time.sleep(1)

    db.session.commit()
    print(f"\nDone. Updated {updated}/{len(props)} properties.")


@click.command('convert-currencies')
@with_appcontext
def convert_currencies_command():
    """Converts all historical property prices from UAH/EUR to USD."""
    from app.services.currency import convert_to_usd

    props = Property.query.filter(Property.currency != 'USD').all()
    print(f"Found {len(props)} properties with non-USD currencies.")

    updated = 0
    for i, p in enumerate(props, 1):
        if not p.price or p.price <= 0:
            continue

        old_price = p.price
        old_curr = p.currency

        new_price = convert_to_usd(old_price, old_curr)
        p.price = new_price
        p.currency = 'USD'
        updated += 1

        print(f"[{i}/{len(props)}] #{p.id}: {old_price} {old_curr} -> {new_price:.0f} USD")

        if i % 100 == 0:
            db.session.commit()

    db.session.commit()
    print(f"\nDone. Converted {updated} properties to USD.")


@click.command('rescrape-duplicates')
@click.option('--min-count', default=20, help='Min duplicate count to flag a price as suspicious')
@click.option('--workers', default=5, help='Number of parallel scrape threads')
@with_appcontext
def rescrape_duplicates_command(min_count, workers):
    """Re-scrapes bon_ua listings with suspiciously duplicated prices."""
    from sqlalchemy import func as sqlfunc

    duplicate_prices = db.session.query(Property.price).filter(
        Property.source_website == 'bon_ua',
        Property.source_url.isnot(None),
    ).group_by(Property.price).having(sqlfunc.count(Property.id) >= min_count).all()

    bad_prices = {r[0] for r in duplicate_prices}
    print(f"Found {len(bad_prices)} suspicious price value(s): {[round(p, 0) for p in bad_prices]}")

    urls = [
        p.source_url for p in Property.query.filter(
            Property.source_website == 'bon_ua',
            Property.price.in_(list(bad_prices)),
        ).all()
    ]
    print(f"Queued {len(urls)} listings for re-scraping...")

    _execute_scraping(urls, workers, scrape_bon_ua_listing)
