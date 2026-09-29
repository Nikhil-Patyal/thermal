import os
import django
import csv

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from hotspots.models import FacilityCandidate
from django.contrib.gis.geos import Point

def load_volcanoes():
    filepath = 'data/volcanoes_data.csv'
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
        
    print("Deleting old volcano candidates...")
    FacilityCandidate.objects.filter(category='Volcano').delete()

    print("Loading Volcano CSV...")
    count = 0
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        candidates = []
        for row in reader:
            try:
                lat = float(row['latitude'])
                lon = float(row['longitude'])
                geom = Point(lon, lat, srid=4326)
                candidates.append(FacilityCandidate(
                    name=row['volcano_name'],
                    category='Volcano',
                    geometry=geom
                ))
                count += 1
                if len(candidates) >= 5000:
                    FacilityCandidate.objects.bulk_create(candidates)
                    candidates = []
            except Exception as e:
                pass
        
        if candidates:
            FacilityCandidate.objects.bulk_create(candidates)

    print(f"Successfully loaded {count} volcanoes.")

if __name__ == '__main__':
    load_volcanoes()
