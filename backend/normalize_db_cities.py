import os
import sys

# Ensure backend directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Property
from app.services.cities import normalize_city

def main():
    app = create_app()
    with app.app_context():
        # Find all distinct cities in the database
        distinct_cities = db.session.query(Property.city).distinct().filter(Property.city != None).all()
        distinct_cities = [c[0] for c in distinct_cities]
        
        print(f"Found {len(distinct_cities)} distinct city names in DB.")
        
        updates_count = 0
        unknown_cities = set()
        
        for raw_city in distinct_cities:
            normalized = normalize_city(raw_city)
            
            if normalized and normalized != raw_city:
                # Need to update
                props_to_update = Property.query.filter_by(city=raw_city).all()
                print(f"Updating {len(props_to_update)} properties: '{raw_city}' -> '{normalized}'")
                
                for p in props_to_update:
                    p.city = normalized
                
                updates_count += len(props_to_update)
            elif not normalized:
                unknown_cities.add(raw_city)
                
        if updates_count > 0:
            db.session.commit()
            print(f"\nSuccessfully updated {updates_count} properties.")
        else:
            print("\nDatabase is already normalized.")
            
        print(f"\nUnknown cities (not in cities.py mapping):")
        for uc in sorted(unknown_cities):
            print(f" - {uc}")

if __name__ == "__main__":
    main()
