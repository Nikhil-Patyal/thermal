import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from hotspots.models import Hotspot
hotspots = Hotspot.objects.filter(predicted_class__icontains='associated')
print(f"Total industrial hotspots: {hotspots.count()}")
strong = hotspots.filter(confidence_score='Strong').count()
low = hotspots.filter(confidence_score='Low').count()
print(f"Strong: {strong}, Low: {low}")
