import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from hotspots.models import Hotspot
from django.db.models import Count
counts = Hotspot.objects.values('predicted_class', 'confidence_score').annotate(c=Count('id'))
for row in counts:
    print(row)
