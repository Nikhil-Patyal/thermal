import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotspots.models import Hotspot

india_hotspots = Hotspot.objects.filter(
    latitude__gte=6, latitude__lte=36,
    longitude__gte=68, longitude__lte=98
)
unclassified = india_hotspots.filter(predicted_class='Unknown / Uncertain').count()
total = india_hotspots.count()
print(f"Total Indian hotspots: {total}")
print(f"Unknown Indian hotspots: {unclassified}")
