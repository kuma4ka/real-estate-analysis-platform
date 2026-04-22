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


@click.command('purge-stale')
@click.option('--workers', default=20, help='Parallel HTTP check threads')
@click.option('--batch', default=500, help='Commit to DB every N deactivated IDs')
@click.option('--dry-run', is_flag=True, default=False, help='Print without updating DB')
@with_appcontext
def purge_stale_command(workers, batch, dry_run):
    """Check every active listing's source_url; mark inactive if 404/410/gone."""
    import requests
    from concurrent.futures import ThreadPoolExecutor, as_completed as _as_completed

    DEAD_STATUSES = {404, 410}

    # Load only the fields needed — plain tuples, not ORM objects, to avoid cross-thread issues
    rows = db.session.execute(
        db.select(Property.id, Property.source_url, Property.images)
        .where(Property.is_active == True)
    ).all()

    total = len(rows)
    print(f"Checking {total} active listings (workers={workers}, dry_run={dry_run})...")

    def check_row(row):
        prop_id, source_url, images = row.id, row.source_url, row.images
        try:
            resp = requests.head(
                source_url,
                timeout=8,
                allow_redirects=True,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; RealEstateBot/1.0)'}
            )
            if resp.status_code in DEAD_STATUSES:
                return prop_id, resp.status_code, 'dead_url'

            if images and len(images) > 0:
                img_resp = requests.head(
                    images[0], timeout=5, allow_redirects=True,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                if img_resp.status_code in {404, 410}:
                    return prop_id, img_resp.status_code, 'dead_image'

            return prop_id, resp.status_code, 'alive'
        except Exception:
            return prop_id, 0, 'timeout'

    dead_ids = []
    checked = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(check_row, row): row for row in rows}
        for future in _as_completed(futures):
            prop_id, status, reason = future.result()
            checked += 1

            if reason in ('dead_url', 'dead_image'):
                dead_ids.append(prop_id)
                print(f"  DEAD #{prop_id} -> HTTP {status} ({reason})")

            if checked % 200 == 0:
                print(f"  [{checked}/{total}] checked -- {len(dead_ids)} dead so far")

    print(f"\n{len(dead_ids)} listings to deactivate out of {total} checked.")

    if not dry_run and dead_ids:
        for i in range(0, len(dead_ids), batch):
            chunk = dead_ids[i:i + batch]
            db.session.execute(
                db.update(Property)
                .where(Property.id.in_(chunk))
                .values(is_active=False)
            )
            db.session.commit()
            print(f"  Committed batch {i // batch + 1}: {len(chunk)} listings deactivated")

    print(f"\nDone. Checked {checked}, deactivated {len(dead_ids)} listings.")
    if dry_run:
        print("  (dry-run: no DB changes made)")
