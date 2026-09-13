import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from hotspots.models import Hotspot
from django.db.models import Count

india_qs = Hotspot.objects.filter(
    latitude__gte=6, latitude__lte=36,
    longitude__gte=68, longitude__lte=98,
    latitude__isnull=False, longitude__isnull=False
)
print(f"Total Indian hotspots: {india_qs.count()}")
for row in india_qs.values('predicted_class').annotate(count=Count('predicted_class')).order_by('-count'):
    print(f"{row['predicted_class']}: {row['count']}")
