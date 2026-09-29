import os
import time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from hotspots.models import Hotspot
from ml.feature_engineering import FeatureExtractor
from ml.evidence_engine import EvidenceEngine

print("Running FAST classification for India & Sri Lanka only...")
extractor = FeatureExtractor()
engine = EvidenceEngine()

# India & Sri Lanka bounding box roughly: Lat 5 to 37, Lon 68 to 98
hotspots_qs = Hotspot.objects.filter(
    latitude__gte=5, latitude__lte=37,
    longitude__gte=68, longitude__lte=98
).order_by('id')

total = hotspots_qs.count()
print(f"Found {total} hotspots in region to classify.")

processed = 0
chunk_size = 500

while processed < total:
    chunk = list(hotspots_qs[processed:processed + chunk_size])
    if not chunk:
        break
        
    X_df = extractor.extract_features(chunk, fit_dbscan=False)
    if X_df.empty:
        processed += len(chunk)
        continue
        
    results_df = engine.generate_weak_labels(X_df)
    
    for hotspot in chunk:
        hid = hotspot.id
        if hid not in results_df.index:
            continue
        res = results_df.loc[hid]
        hotspot.predicted_class = res['label']
        hotspot.confidence_score = res.get('label_confidence_str')
        hotspot.attribution_status = res.get('attribution_status')
        hotspot.is_tentative = res.get('is_tentative', False)
        hotspot.evidence_strength = res.get('label_confidence_str')
        
    Hotspot.objects.bulk_update(chunk, ['predicted_class', 'confidence_score', 'attribution_status', 'is_tentative', 'evidence_strength'])
    processed += len(chunk)
    print(f"Processed {processed}/{total}...")

print("Fast classification complete!")
