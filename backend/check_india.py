import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotspots.models import Hotspot

# India bounding box roughly: lat 6 to 36, lon 68 to 98
india_hotspots = Hotspot.objects.filter(
    latitude__gte=6, latitude__lte=36,
    longitude__gte=68, longitude__lte=98
)
print(f"Total Indian hotspots in DB: {india_hotspots.count()}")
print(f"Top 5 Indian hotspots FRP: {[h.frp for h in india_hotspots.order_by('-frp')[:5]]}")
