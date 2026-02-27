import click
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask.cli import with_appcontext
from app import db, create_app
from app.models import Property
from app.services.meget import scrape_meget_listing, get_listing_urls as meget_get_listing_urls
from app.services.bon_ua import scrape_bon_ua_listing, get_listing_urls as bon_ua_get_listing_urls
from app.services.cities import get_center, normalize_city, get_region_center
from app.services.listing_validator import ListingValidator

from geopy.geocoders import Photon
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from app.services.address_normalizer import AddressNormalizer
from geopy.distance import geodesic


def get_lat_long(address, region=None, attempt=1):
    try:
        geolocator = Photon(user_agent="meget_scraper_v3")

        candidates = AddressNormalizer.normalize(address)
        if not candidates:
            candidates = [address]

        cleaned_addr = AddressNormalizer._basic_clean(address)
        parts = cleaned_addr.split(',')
        expected_city = None
        if parts:
            possible_city = parts[0].strip()
            expected_city = normalize_city(possible_city)

        if expected_city and len(candidates) == 1:
            canonical = normalize_city(candidates[0])
            if canonical == expected_city:
                center = get_center(expected_city)
                if center:
                    return center[0], center[1], f"{expected_city}, Україна", "city"

        if region:
            region = region.strip()

        for candidate in candidates:
            try:
                query_parts = [candidate]

                if expected_city and expected_city not in candidate:
                    query_parts.append(expected_city)
                if region and region not in candidate:
                    query_parts.append(region)
                if "Україна" not in candidate and "Ukraine" not in candidate:
                    query_parts.append("Україна")

                query = ", ".join(query_parts)
                query = ", ".join(p.strip() for p in query.split(",") if p.strip())
                print(f"    Geocoding: '{query}'")

                location = geolocator.geocode(query, timeout=10)

                if location:
                    # Region validation
                    if region:
                        region_result = get_region_center(region)
                        if region_result:
                            _, reg_city = region_result
                            from app.services.cities import CITIES
                            city_info = CITIES.get(reg_city, {})
                            all_names = [reg_city.lower()] + [a.lower() for a in city_info.get('aliases', [])]
                            loc_addr_lower = location.address.lower()
                            if not any(name in loc_addr_lower for name in all_names):
                                print(f"    ⚠️ Region mismatch: {location.address}")
                                continue

                    # City-level distance check (30km)
                    if expected_city:
                        center = get_center(expected_city)
                        if center:
                            dist_km = geodesic((location.latitude, location.longitude), center).km
                            if dist_km > 30:
                                print(f"    ⚠️ Too far ({dist_km:.0f}km from {expected_city})")
                                continue
                    # Oblast-level distance check (100km)
                    elif region:
                        region_result = get_region_center(region)
                        if region_result:
                            reg_center, reg_city = region_result
                            dist_km = geodesic((location.latitude, location.longitude), reg_center).km
                            if dist_km > 100:
                                print(f"    ⚠️ Too far ({dist_km:.0f}km from {reg_city}, {region})")
                                continue

                    return location.latitude, location.longitude, location.address, "exact"

            except (GeocoderTimedOut, GeocoderServiceError) as e:
                print(f"    ⚠️ Photon error: {e}")
                continue

        # Fallback to oblast center
        if region:
            region_result = get_region_center(region)
            if region_result:
                reg_center, reg_city = region_result
                print(f"    📍 Falling back to region center: {reg_city}")
                return reg_center[0], reg_center[1], f"{reg_city}, Україна", "city"

        return None, None, None, None
    except Exception as e:
        print(f"⚠️ Geocoding error: {e}")
        return None, None, None, None


def process_url_in_thread(url, app_config, scrape_func):
    app = create_app(app_config)

    with app.app_context():
        time.sleep(0.5)

        data = scrape_func(url)
        if not data:
            return {'status': 'error', 'url': url, 'msg': 'Scrape failed'}

        # Normalize currency to USD using live NBU rates
        from app.services.currency import convert_to_usd
        raw_price = data.get('price', 0)
        raw_currency = data.get('currency', 'UAH')
        
        # We only convert if price > 0
        if raw_price > 0 and raw_currency != 'USD':
            data['price'] = convert_to_usd(raw_price, raw_currency)
            data['currency'] = 'USD'

        is_valid, rejection_reason = ListingValidator.validate(data)

        try:
            existing_prop = Property.query.filter_by(source_url=url).first()

            if existing_prop:
                needs_update = False
                changes = []

                if existing_prop.price != data['price'] or existing_prop.currency != data['currency']:
                    existing_prop.price = data['price']
                    existing_prop.currency = data['currency']
                    changes.append("price")
                    needs_update = True

                if existing_prop.source_website != data.get('source_website'):
                    existing_prop.source_website = data.get('source_website')
                    changes.append("source")
                    needs_update = True

                if data.get('address') and existing_prop.address != data['address']:
                    print(f"DEBUG: Updating address from '{existing_prop.address}' to '{data['address']}'")
                    existing_prop.address = data['address']
                    existing_prop.city = data.get('city')
                    existing_prop.district = data.get('district')
                    changes.append("address")
                    needs_update = True
                else:
                    print(f"DEBUG: Skipping UPDATE string check. DB address: {existing_prop.address} | New: {data.get('address')}")
                    
                # Force a new geocode attempt for the new address
                if "address" in changes:
                    lat, lng, canonical_addr, precision = get_lat_long(
                        data['address'], region=data.get('region')
                    )
                    if lat and lng:
                        existing_prop.latitude = lat
                        existing_prop.longitude = lng
                        existing_prop.geocode_precision = precision
                        if canonical_addr:
                            existing_prop.address = canonical_addr
                        changes.append("geolocation")
                    else:
                        existing_prop.latitude = None
                        existing_prop.longitude = None
                        existing_prop.geocode_precision = None
                
                # Only attempt backfill if the address string wasn't just changed, and we lack coords
                elif not existing_prop.latitude and existing_prop.address:
                    lat, lng, canonical_addr, precision = get_lat_long(
                        existing_prop.address, region=data.get('region')
                    )
                    if lat and lng:
                        existing_prop.latitude = lat
                        existing_prop.longitude = lng
                        existing_prop.geocode_precision = precision
                        if canonical_addr:
                            existing_prop.address = canonical_addr
                        changes.append("geolocation (backfill)")
                        needs_update = True

                if not existing_prop.images and data['images']:
                    existing_prop.images = data['images']
                    changes.append("images")
                    needs_update = True

                if needs_update:
                    if not is_valid:
                        changes.append(f"flagged: {rejection_reason}")
                    
                    print(f"DEBUG: Committing to DB. needs_update={needs_update}, is_valid={is_valid}, changes={changes}, new address={existing_prop.address}")
                    existing_prop.updated_at = datetime.utcnow()
                    db.session.commit()
                    
                    if not is_valid:
                        return {'status': 'rejected', 'url': url, 'msg': f"Updated but flagged: {rejection_reason}"}
                    return {'status': 'updated', 'title': data['title'], 'msg': ', '.join(changes)}
                else:
                    if not is_valid:
                        return {'status': 'rejected', 'url': url, 'msg': rejection_reason}
                    return {'status': 'skipped', 'url': url}
            else:
                if not is_valid:
                    return {'status': 'rejected', 'url': url, 'msg': rejection_reason}

                lat, lng, canonical_addr, precision = None, None, None, None
                if data.get('address'):
                    lat, lng, canonical_addr, precision = get_lat_long(
                        data['address'], region=data.get('region')
                    )

                new_prop = Property(
                    title=data['title'],
                    source_url=data['source_url'],
                    source_website=data['source_website'],
                    price=data.get('price'),
                    currency=data.get('currency'),
                    address=canonical_addr if canonical_addr else data.get('address'),
                    city=data.get('city'),
                    district=data.get('district'),
                    latitude=lat,
                    longitude=lng,
                    geocode_precision=precision,
                    area=data.get('area'),
                    rooms=data.get('rooms'),
                    images=data.get('images'),
                    description=f"Scraped from {data['source_website']}"
                )
                db.session.add(new_prop)
                db.session.commit()
                return {'status': 'new', 'title': data['title'], 'price': data['price'], 'currency': data['currency']}

        except Exception as e:
            db.session.rollback()
            return {'status': 'error', 'url': url, 'msg': str(e)}


@click.command(name='scrape_meget')
@click.option('--workers', default=5, help='Number of parallel threads')
@click.option('--pages', default=1, help='Number of pages to scrape from global catalog')
@with_appcontext
def scrape_meget_command(workers, pages):
    print(f"🚀 Starting Meget scraping with {workers} threads, {pages} pages...")

    all_target_urls = set()
    for page in range(1, pages + 1):
        print(f"[CRAWLER] Page {page}...")
        urls = meget_get_listing_urls(page=page)
        if urls:
            all_target_urls.update(urls)
        time.sleep(1)

    url_list = list(all_target_urls)
    _execute_scraping(url_list, workers, scrape_meget_listing)

@click.command(name='scrape_bon_ua')
@click.option('--workers', default=5, help='Number of parallel threads')
@click.option('--pages', default=1, help='Number of pages to scrape from global catalog')
@with_appcontext
def scrape_bon_ua_command(workers, pages):
    print(f"🚀 Starting Bon.ua scraping with {workers} threads, {pages} pages...")

    all_target_urls = set()
    for page in range(1, pages + 1):
        print(f"[CRAWLER] Page {page}...")
        urls = bon_ua_get_listing_urls(page=page)
        if urls:
            all_target_urls.update(urls)
        time.sleep(1)

    url_list = list(all_target_urls)
    _execute_scraping(url_list, workers, scrape_bon_ua_listing)


def _execute_scraping(url_list, workers, scrape_func):
    total = len(url_list)

    if total == 0:
        print("No listings found.")
        return

    print(f"📋 {total} listings queued. Processing...")

    from config import Config
    stats = {'new': 0, 'updated': 0, 'skipped': 0, 'rejected': 0, 'errors': 0}

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(process_url_in_thread, url, Config, scrape_func): url
            for url in url_list
        }

        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            status = result['status']

            if status == 'new':
                stats['new'] += 1
                curr = result.get('currency', 'UAH')
                print(f"[{i}/{total}] ✅ {result['title'][:40]}... ({result['price']} {curr})")
            elif status == 'updated':
                stats['updated'] += 1
                print(f"[{i}/{total}] 🔄 {result['title'][:40]}... ({result['msg']})")
            elif status == 'skipped':
                stats['skipped'] += 1
            elif status == 'rejected':
                stats['rejected'] += 1
                print(f"[{i}/{total}] 🚫 {result['msg']}")
            elif status == 'error':
                stats['errors'] += 1
                print(f"[{i}/{total}] ❌ {result['msg']}")

    print(f"\n📊 Done: {stats['new']} new, {stats['updated']} updated, {stats['skipped']} skipped, {stats['rejected']} rejected, {stats['errors']} errors")


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

    # Find prices that appear too often (suspiciously)
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
