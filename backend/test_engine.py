import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from ml.evidence_engine import EvidenceEngine
from hotspots.models import Hotspot
engine = EvidenceEngine()
hotspots = Hotspot.objects.filter(predicted_class__icontains='associated').exclude(confidence_score='Strong')[:10]
for h in hotspots:
    match = engine._check_facility_overlap(h.longitude, h.latitude, h.scan, h.track)
    print(h.id, h.predicted_class, match)
