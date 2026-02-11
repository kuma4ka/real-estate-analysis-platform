import click
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask.cli import with_appcontext
from app import db, create_app
from app.models import Property
from app.services.meget import scrape_meget_listing, get_listing_urls


from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

def get_lat_long(address, attempt=1):
    try:
        geolocator = Nominatim(user_agent="meget_scraper_v2")
        
        # Helper to clean address for geocoding
        def clean_for_geocoding(addr):
            # Remove "область", "район", "р-н" which confuse Nominatim sometimes
            import re
            cleaned = re.sub(r'\b(область|район|р-н)\b', '', addr, flags=re.IGNORECASE)
            # Remove "No." "№" etc
            cleaned = re.sub(r'[№#]', '', cleaned)
            # Remove multiple spaces/commas
            cleaned = re.sub(r'\s*,\s*', ', ', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned)
            return cleaned.strip(", ")

        # Attempt 1: Raw address + Country
        location = geolocator.geocode(f"{address}, Ukraine", timeout=10)
        
        # Verify city match to avoid "Dnipro district in Kyiv" issues
        if location and "Kyiv" in location.address and "Днепр" in address and "Киев" not in address:
             print(f"   ⚠️ Suspicious match for {address}: {location.address}. Ignoring.")
             location = None

        # Attempt 2: Cleaned address 
        if not location:
            cleaned = clean_for_geocoding(address)
            if cleaned != address:
                 # Check if we can extract city for structured query
                 # This is safer than string concatenation
                 search_query = f"{cleaned}, Ukraine"
                 print(f"   ⚠️ Geocoding retry with cleaned: '{search_query}'")
                 location = geolocator.geocode(search_query, timeout=10)

        # Attempt 3: Simplified "City, Street"
        if not location:
             parts = [p.strip() for p in address.split(',')]
             if len(parts) > 2:
                 simplified = f"{parts[0]}, {', '.join(parts[-2:])}"
                 if simplified != address and simplified != cleaned:
                     print(f"   ⚠️ Geocoding retry with simplified: '{simplified}'")
                     location = geolocator.geocode(f"{simplified}, Ukraine", timeout=10)
                     
        # Final check for cross-city contamination
        if location:
             # If original address said "Dnipro" but result is "Kyiv", reject it unless context implies it.
             # Simple heuristic: if city name is in valid UA cities, check if result contains it.
             # existing_prop.city is passed to us? No, we only have address string here. 
             # But address usually starts with City.
             pass

        if location:
            return location.latitude, location.longitude
        return None, None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"⚠️ Geocoding error for {address}: {e}")
        return None, None
    except Exception as e:
        print(f"⚠️ Unexpected geocoding error: {e}")
        return None, None

def process_url_in_thread(url, app_config):
    app = create_app(app_config)

    with app.app_context():
        # Small delay to respect scraper and geocoder limits
        time.sleep(0.5) 
        
        data = scrape_meget_listing(url)
        if not data:
            return {'status': 'error', 'url': url, 'msg': 'Scrape failed'}

        try:
            existing_prop = Property.query.filter_by(source_url=url).first()

            if existing_prop:
                needs_update = False
                changes = []

                if existing_prop.price != data['price']:
                    existing_prop.price = data['price']
                    existing_prop.currency = data['currency']
                    changes.append("price")
                    needs_update = True

                if data['address'] and existing_prop.address != data['address']:
                    existing_prop.address = data['address']
                    existing_prop.city = data['city']
                    existing_prop.district = data['district']
                    
                    # Geocode new address
                    lat, lng = get_lat_long(data['address'])
                    if lat and lng:
                        existing_prop.latitude = lat
                        existing_prop.longitude = lng
                        changes.append("geolocation")
                    
                    if "address" not in changes: 
                        changes.append("address")
                    needs_update = True
                
                # If address didn't change but we don't have coords, try to geocode
                if not existing_prop.latitude and existing_prop.address:
                    lat, lng = get_lat_long(existing_prop.address)
                    if lat and lng:
                        existing_prop.latitude = lat
                        existing_prop.longitude = lng
                        changes.append("geolocation (backfill)")
                        needs_update = True
                    else:
                        print(f"Failed to update geocode for {data['address']}")

                if not existing_prop.images and data['images']:
                    existing_prop.images = data['images']
                    changes.append("images")
                    needs_update = True

                if needs_update:
                    existing_prop.updated_at = datetime.utcnow()
                    db.session.commit()
                    return {'status': 'updated', 'title': data['title'], 'msg': ', '.join(changes)}
                else:
                    return {'status': 'skipped', 'url': url}
            else:
                # Geocode new property
                lat, lng = None, None
                if data.get('address'):
                    lat, lng = get_lat_long(data['address'])

                new_prop = Property(
                    title=data['title'],
                    source_url=data['source_url'],
                    source_website='meget',
                    price=data.get('price'),
                    currency=data.get('currency'),
                    address=data.get('address'),
                    city=data.get('city'),
                    district=data.get('district'),
                    latitude=lat,
                    longitude=lng,
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
def scrape_command(workers, pages):
    print(f"🚀 Starting GLOBAL scraping with {workers} threads...")

    all_target_urls = set()

    for page in range(1, pages + 1):
        print(f"[CRAWLER] Scanning Global Catalog Page {page}...")
        urls = get_listing_urls(page=page)
        if urls:
            all_target_urls.update(urls)
        time.sleep(1)

    url_list = list(all_target_urls)
    total_urls = len(url_list)

    if total_urls == 0:
        print("[STOP] No listings found.")
        return

    print(f"📦 Queue size: {total_urls} listings. Processing parallel...")

    from config import Config
    stats = {'new': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_url = {
            executor.submit(process_url_in_thread, url, Config): url
            for url in url_list
        }

        for i, future in enumerate(as_completed(future_to_url), 1):
            result = future.result()

            status = result['status']
            if status == 'new':
                stats['new'] += 1
                curr = result.get('currency', 'UAH')
                print(f"[{i}/{total_urls}] ✅ NEW: {result['title'][:30]}... ({result['price']} {curr})")
            elif status == 'updated':
                stats['updated'] += 1
                print(f"[{i}/{total_urls}] 🔄 UPD: {result['title'][:30]}... ({result['msg']})")
            elif status == 'skipped':
                stats['skipped'] += 1
            elif status == 'error':
                stats['errors'] += 1
                print(f"[{i}/{total_urls}] ❌ ERR: {result['msg']}")

    print("-" * 40)
    print(
        f"🏁 FINISHED. New: {stats['new']} | Updated: {stats['updated']} | Skipped: {stats['skipped']} | Errors: {stats['errors']}")