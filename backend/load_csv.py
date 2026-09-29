import os
import django
import csv

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from hotspots.models import FacilityCandidate
from django.contrib.gis.geos import Point

def load_data():
    filepath = 'data/industrial_and_mines_data.csv'
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
        
    print("Clearing old FacilityCandidates...")
    FacilityCandidate.objects.all().delete()

    print("Loading CSV...")
    count = 0
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        candidates = []
        for row in reader:
            try:
                lat = float(row['Latitude'])
                lon = float(row['Longitude'])
                # Point takes (x, y) -> (longitude, latitude)
                geom = Point(lon, lat, srid=4326)
                candidates.append(FacilityCandidate(
                    name=row['Name'],
                    category=row['Category'],
                    geometry=geom
                ))
                count += 1
                if len(candidates) >= 5000:
                    FacilityCandidate.objects.bulk_create(candidates)
                    candidates = []
                    print(f"Loaded {count}...")
            except Exception as e:
                pass
        
        if candidates:
            FacilityCandidate.objects.bulk_create(candidates)
            print(f"Loaded {count}...")

    print(f"Successfully loaded {count} facilities.")

if __name__ == '__main__':
    load_data()
