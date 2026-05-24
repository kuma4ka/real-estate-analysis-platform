import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from geopy.geocoders import ArcGIS
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from geopy.distance import geodesic

from app import db, create_app
from app.models import Property
from app.services.cities import get_center, normalize_city, get_region_center
from app.services.address_normalizer import AddressNormalizer
from app.services.listing_validator import ListingValidator

_arcgis = ArcGIS(timeout=10)

def _geocode_with_fallback(query: str):
    """Use ArcGIS as the primary free geocoder to avoid strict Nominatim/Photon limits."""
    try:
        location = _arcgis.geocode(query)
        if location:
            return location
    except (GeocoderTimedOut, GeocoderServiceError, Exception) as e:
        print(f"    ⚠️ ArcGIS error: {e}")
    return None


def get_lat_long(address, region=None, attempt=1):
    try:
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

            location = _geocode_with_fallback(query)

            if location:
                UA_LAT = (44.0, 52.5)
                UA_LNG = (22.0, 40.5)
                if not (UA_LAT[0] <= location.latitude <= UA_LAT[1] and
                        UA_LNG[0] <= location.longitude <= UA_LNG[1]):
                    print("    ⚠️ Outside Ukraine: Coords hidden")
                    continue

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

                if expected_city:
                    center = get_center(expected_city)
                    if center:
                        dist_km = geodesic((location.latitude, location.longitude), center).km
                        if dist_km > 30:
                            print(f"    ⚠️ Too far ({dist_km:.0f}km from {expected_city})")
                            continue
                elif region:
                    region_result = get_region_center(region)
                    if region_result:
                        reg_center, reg_city = region_result
                        dist_km = geodesic((location.latitude, location.longitude), reg_center).km
                        if dist_km > 100:
                            print(f"    ⚠️ Too far ({dist_km:.0f}km from {reg_city}, {region})")
                            continue

                return location.latitude, location.longitude, location.address, "exact"

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



def process_url_in_thread(url, app, scrape_func):
    with app.app_context():
        time.sleep(0.5)

        data = scrape_func(url)
        if not data:
            try:
                expired = Property.query.filter_by(source_url=url).first()
                if expired and expired.is_active:
                    expired.is_active = False
                    db.session.commit()
                    return {'status': 'error', 'url': url, 'msg': 'Listing expired - marked inactive'}
            except Exception:
                pass
            return {'status': 'error', 'url': url, 'msg': 'Scrape failed'}

        from app.services.currency import convert_to_usd
        raw_price = data.get('price', 0)
        raw_currency = data.get('currency', 'UAH')

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
                    existing_prop.address = data['address']
                    existing_prop.city = data.get('city')
                    existing_prop.district = data.get('district')
                    changes.append("address")
                    needs_update = True

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

                    existing_prop.updated_at = datetime.now(timezone.utc)
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
                    city=normalize_city(data.get('city')) or data.get('city') if data.get('city') else None,
                    district=data.get('district'),
                    latitude=lat,
                    longitude=lng,
                    geocode_precision=precision,
                    area=data.get('area'),
                    rooms=data.get('rooms'),
                    images=data.get('images'),
                )
                db.session.add(new_prop)
                db.session.commit()
                return {'status': 'new', 'title': data['title'], 'price': data['price'], 'currency': data['currency']}

        except Exception as e:
            db.session.rollback()
            return {'status': 'error', 'url': url, 'msg': str(e)}


def _execute_scraping(url_list, workers, scrape_func):
    total = len(url_list)

    if total == 0:
        print("No listings found.")
        return

    print(f"📋 {total} listings queued. Processing...")

    from flask import current_app
    app = current_app._get_current_object()
    stats = {'new': 0, 'updated': 0, 'skipped': 0, 'rejected': 0, 'errors': 0}

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(process_url_in_thread, url, app, scrape_func): url
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
