import os
import django
import json
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotspots.models import Hotspot
from django.db.models import Count, Q

print("=== HOTSPOT BASELINE AUDIT ===")
total = Hotspot.objects.count()
print(f"Total Detections: {total}")

print("\n--- Class Counts & Percentages ---")
classes = Hotspot.objects.values('predicted_class').annotate(c=Count('id')).order_by('-c')
for cl in classes:
    pct = (cl['c'] / total) * 100 if total > 0 else 0
    print(f"{cl['predicted_class']}: {cl['c']} ({pct:.2f}%)")

print("\n--- Missing Field Rates ---")
missing_frp = Hotspot.objects.filter(frp__isnull=True).count()
missing_bright = Hotspot.objects.filter(brightness__isnull=True).count()
print(f"Missing FRP: {missing_frp} ({(missing_frp/total)*100:.2f}%)")
print(f"Missing Brightness: {missing_bright} ({(missing_bright/total)*100:.2f}%)")

