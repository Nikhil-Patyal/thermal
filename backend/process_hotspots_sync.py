import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotspots.models import Hotspot
import hotspots.tasks
from hotspots.tasks import enrich_hotspot_data, classify_hotspot

# Mock the delay function so it runs synchronously without touching Redis
def fake_delay(*args, **kwargs):
    return classify_hotspot(*args, **kwargs)

hotspots.tasks.classify_hotspot.delay = fake_delay

def enrich_and_classify_all():
    hotspots_qs = Hotspot.objects.filter(predicted_class__isnull=True)
    count = hotspots_qs.count()
    print(f"Found {count} hotspots needing enrichment and classification.")
    
    for i, h in enumerate(hotspots_qs):
        print(f"Processing hotspot {i+1}/{count} (ID {h.id})...")
        try:
            # This will internally call our fake_delay for classify_hotspot
            enrich_hotspot_data(h.id)
        except Exception as e:
            print(f"Error processing {h.id}: {e}")
            
if __name__ == '__main__':
    enrich_and_classify_all()
