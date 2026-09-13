import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from hotspots.models import Hotspot, FacilityCandidate
from django.contrib.gis.measure import D

hotspots = Hotspot.objects.filter(latitude__gte=6, latitude__lte=36, longitude__gte=68, longitude__lte=98)
matches = 0
for h in hotspots:
    if FacilityCandidate.objects.filter(geometry__distance_lte=(h.geometry, D(m=5000))).exists():
        matches += 1
print(f"Hotspots within 5000m of an industrial facility: {matches}")
