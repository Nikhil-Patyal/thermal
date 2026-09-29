import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotspots.models import Hotspot
from django.db.models import Count, Q

total = Hotspot.objects.count()
print(f"Total Hotspots: {total}")

# Breakdown by predicted_class
print("\nPredicted Class Distribution:")
for item in Hotspot.objects.values('predicted_class').annotate(count=Count('id')).order_by('-count'):
    print(f"  {item['predicted_class']}: {item['count']}")

# Breakdown by attribution_status
print("\nAttribution Status Distribution:")
for item in Hotspot.objects.values('attribution_status').annotate(count=Count('id')).order_by('-count'):
    print(f"  {item['attribution_status']}: {item['count']}")

# Diagnosis reasons
print("\nDiagnosis:")
enrichment_never_ran = Hotspot.objects.filter(attribution_status='pending_enrichment').count()
missing_raster = Hotspot.objects.filter(attribution_status='insufficient_landcover').count()
mixed_landcover = Hotspot.objects.filter(is_tentative=True).count()
industrial = Hotspot.objects.filter(industrial_anomaly_status__isnull=False).count()

print(f"  Pending Enrichment (or missing raster): {enrichment_never_ran}")
print(f"  Insufficient Landcover (bad pixels): {missing_raster}")
print(f"  Mixed Landcover (Tentative): {mixed_landcover}")
print(f"  Industrial matches: {industrial}")

# How many actually have landcover data?
has_lc = Hotspot.objects.filter(valid_coverage__isnull=False).count()
print(f"\nHotspots with actual landcover data (valid_coverage is not null): {has_lc}")
