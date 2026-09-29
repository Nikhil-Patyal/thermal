import os
import django
import csv
from django.contrib.gis.geos import Point

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotspots.models import FacilityCandidate
from django.db import transaction

print("Loading coarse CSV into DB as a temporary fast-track...")
FacilityCandidate.objects.all().delete()

batch = []
with open('data/industrial_and_mines_data.csv', 'r') as f:
    reader = csv.DictReader(f)
    with transaction.atomic():
        for row in reader:
            try:
                lat = float(row['Latitude'])
                lon = float(row['Longitude'])
                batch.append(FacilityCandidate(
                    name=row['Name'],
                    category=row['Category'],
                    geometry=Point(lon, lat)
                ))
            except Exception:
                pass
        FacilityCandidate.objects.bulk_create(batch)
print(f"Loaded {len(batch)} coarse facilities.")
