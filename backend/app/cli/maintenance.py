import os
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
    query = Property.query.filter(Property.address.isnot(None))
    total = query.count()
    click.echo(f"Re-geocoding {total} properties...")

    count = 0
    for p in query.yield_per(100):
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
                click.echo(f"Updated {count}")
                time.sleep(1)
        else:
            p.latitude = None
            p.longitude = None
            p.geocode_precision = None

    db.session.commit()
    click.echo(f"Done. Updated {count}/{total}.")


@click.command(name='regeocode_ids')
@click.argument('ids', nargs=-1, type=int, required=True)
@with_appcontext
def regeocode_ids_command(ids):
    """Re-geocode specific properties by ID. Pass IDs as space-separated arguments.

    Example: flask regeocode_ids 1 2 3 42
    """
    click.echo(f"Re-geocoding {len(ids)} properties: {list(ids)}")

    props = Property.query.filter(Property.id.in_(ids)).all()

    for p in props:
        click.echo(f"#{p.id}: Processing...")
        lat, lng, canonical, precision = get_lat_long(p.address)
        if lat and lng:
            click.echo("  [OK]  Geocoded")
            p.latitude = lat
            p.longitude = lng
            p.geocode_precision = precision
            if canonical:
                p.address = canonical
        else:
            click.echo("  [FAIL] Could not geocode")
            p.latitude = None
            p.longitude = None
            p.geocode_precision = None

    db.session.commit()
    click.echo("Done.")


@click.command('backfill-images')
@click.option('--limit', default=0, help='Max properties to process (0 = all)')
@with_appcontext
def backfill_images(limit):
    """Re-fetch images for properties that have none."""
    from app.services.meget import fetch_html as meget_fetch_html
    from app.services.meget.parser import ListingParser as MegetParser
    from app.services.bon_ua.network import fetch_html as bon_fetch_html
    from app.services.bon_ua.parser import BonUaParser

    query = Property.query.filter(
        db.or_(Property.images.is_(None), Property.images == '[]')
    ).filter(Property.source_url.isnot(None))

    if limit > 0:
        query = query.limit(limit)

    props = query.all()
    click.echo(f"Found {len(props)} properties without images.")

    updated = 0
    for i, p in enumerate(props, 1):
        click.echo(f"[{i}/{len(props)}] #{p.id}: {p.source_url}")

        images = []
        if p.source_website == 'bon_ua':
            html = bon_fetch_html(p.source_url)
            if html:
                parser = BonUaParser(html, p.source_url)
                images = parser.get_images()
        else:
            soup = meget_fetch_html(p.source_url)
            if soup:
                parser = MegetParser(soup, p.source_url)
                images = parser.get_images()

        if not images:
            click.echo("  [SKIP] Could not fetch or no images found")
            time.sleep(1)
            continue

        p.images = images
        updated += 1
        click.echo(f"  [OK]   Found {len(images)} image(s)")

        if i % 25 == 0:
            db.session.commit()

        time.sleep(1)

    db.session.commit()
    click.echo(f"\nDone. Updated {updated}/{len(props)} properties.")



@click.command('convert-currencies')
@with_appcontext
def convert_currencies_command():
    """Converts all historical property prices from UAH/EUR to USD."""
    from app.services.currency import convert_to_usd

    total = Property.query.filter(Property.currency != 'USD').count()
    click.echo(f"Found {total} properties with non-USD currencies.")

    updated = 0
    i = 0
    for p in Property.query.filter(Property.currency != 'USD').yield_per(500):
        i += 1
        if not p.price or p.price <= 0:
            continue

        old_price = p.price
        old_curr = p.currency

        new_price = convert_to_usd(old_price, old_curr)
        p.price = new_price
        p.currency = 'USD'
        updated += 1

        click.echo(f"[{i}/{total}] #{p.id}: {old_price} {old_curr} -> {new_price:.0f} USD")

        if updated % 100 == 0:
            db.session.commit()

    db.session.commit()
    click.echo(f"\nDone. Converted {updated} properties to USD.")



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
    click.echo(f"Found {len(bad_prices)} suspicious price value(s): {[round(p, 0) for p in bad_prices]}")

    urls = [
        p.source_url for p in Property.query.filter(
            Property.source_website == 'bon_ua',
            Property.price.in_(list(bad_prices)),
        ).all()
    ]
    click.echo(f"Queued {len(urls)} listings for re-scraping...")

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

    # Load only the fields needed ?   plain tuples, not ORM objects, to avoid cross-thread issues
    rows = db.session.execute(
        db.select(Property.id, Property.source_url, Property.images)
        .where(Property.is_active == True)
    ).all()

    total = len(rows)
    click.echo(f"Checking {total} active listings (workers={workers}, dry_run={dry_run})...")

    def check_row(row, session: requests.Session):
        prop_id, source_url, images = row.id, row.source_url, row.images
        try:
            from urllib.parse import urlparse
            import socket
            import ipaddress

            parsed = urlparse(source_url)
            if parsed.scheme not in ('http', 'https') or not parsed.hostname:
                return prop_id, 0, 'invalid_url'

            try:
                resolved_ip = socket.getaddrinfo(parsed.hostname, None)[0][4][0]
                ip_obj = ipaddress.ip_address(resolved_ip)
            except (socket.gaierror, ValueError):
                return prop_id, 0, 'invalid_url'

            if (
                ip_obj.is_loopback
                or ip_obj.is_private
                or ip_obj.is_link_local
                or ip_obj.is_reserved
                or ip_obj.is_multicast
                or ipaddress.ip_address(resolved_ip) in ipaddress.ip_network('100.64.0.0/10')
            ):
                return prop_id, 0, 'invalid_url'

            resp = session.head(
                source_url,
                timeout=8,
                allow_redirects=True,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; RealEstateBot/1.0)'}
            )
            if resp.status_code in DEAD_STATUSES:
                return prop_id, resp.status_code, 'dead_url'

            if images and len(images) > 0:
                img_resp = session.head(
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
        futures = {executor.submit(check_row, row, requests.Session()): row for row in rows}
        for future in _as_completed(futures):
            prop_id, status, reason = future.result()
            checked += 1

            if reason in ('dead_url', 'dead_image'):
                dead_ids.append(prop_id)
                click.echo(f"  DEAD #{prop_id} -> HTTP {status} ({reason})")

            if checked % 200 == 0:
                click.echo(f"  [{checked}/{total}] checked -- {len(dead_ids)} dead so far")

    click.echo(f"\n{len(dead_ids)} listings to deactivate out of {total} checked.")

    if not dry_run and dead_ids:
        for i in range(0, len(dead_ids), batch):
            chunk = dead_ids[i:i + batch]
            db.session.execute(
                db.update(Property)
                .where(Property.id.in_(chunk))
                .values(is_active=False)
            )
            db.session.commit()
            click.echo(f"  Committed batch {i // batch + 1}: {len(chunk)} listings deactivated")

    click.echo(f"\nDone. Checked {checked}, deactivated {len(dead_ids)} listings.")
    if dry_run:
        click.echo("  (dry-run: no DB changes made)")


@click.command('purge-tokens')
@with_appcontext
def purge_tokens_command():
    """Purges expired JWT tokens from the TokenBlocklist."""
    from datetime import datetime, timezone, timedelta
    from app.models import TokenBlocklist

    expiry_hours = int(os.getenv('JWT_EXPIRY_HOURS', '24'))
    expiration_threshold = datetime.now(timezone.utc) - timedelta(hours=expiry_hours)

    deleted_count = db.session.query(TokenBlocklist).filter(TokenBlocklist.created_at < expiration_threshold).delete()
    db.session.commit()

    click.echo(f"Purged {deleted_count} expired tokens from blocklist (threshold: {expiry_hours}h).")

