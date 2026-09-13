"""
Batch classification module — runs strict rule-based EvidenceEngine on all hotspots in bulk.
All enrichment must be completed before calling this module.
"""
import os
import time
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from hotspots.models import Hotspot
from ml.feature_engineering import FeatureExtractor
from ml.evidence_engine import EvidenceEngine

def batch_classify_all(chunk_size=500):
    """Classify all hotspots in bulk, updating the DB via bulk_update.
    Assumes that all enrichment fields (weather, air_quality, etc.) are present.
    """
    total = Hotspot.objects.count()
    if total == 0:
        print("✅ No hotspots to classify.")
        return

    extractor = FeatureExtractor()
    engine = EvidenceEngine()
    processed = 0
    start_time = time.time()

    while processed < total:
        hotspots_qs = Hotspot.objects.all().order_by('id')[processed:processed + chunk_size]
        hotspots = list(hotspots_qs)
        if not hotspots:
            break

        # Feature extraction – no DBSCAN fitting in batch to save time/complexity
        X_df = extractor.extract_features(hotspots, fit_dbscan=False)
        if X_df.empty:
            print("⚠️ Feature extraction returned empty DataFrame for chunk starting at", processed)
            processed += len(hotspots)
            continue
            
        results_df = engine.generate_weak_labels(X_df)

        for i, hotspot in enumerate(hotspots):
            hid = hotspot.id
            if hid not in results_df.index:
                continue
                
            res = results_df.loc[hid]
            hotspot.predicted_class = res['label']
            hotspot.confidence_score = float(res['label_confidence']) if pd.notna(res['label_confidence']) else 0.0
            
            output_payload = {
                "class": res['label'],
                "probability": float(res['label_confidence']) if pd.notna(res['label_confidence']) else None,
                "confidence": float(res['label_confidence']) if pd.notna(res['label_confidence']) else None,
                "evidence": res.get('label_evidence', []),
                "features_used": [], 
                "data_sources": res.get('label_sources', []),
                "missing_sources": res.get('missing_sources', [])
            }
            hotspot.shap_values = output_payload

        # Bulk update the fields we changed
        Hotspot.objects.bulk_update(
            hotspots,
            ['predicted_class', 'confidence_score', 'shap_values'],
            batch_size=chunk_size,
        )

        processed += len(hotspots)
        print(f"✅ Processed {processed}/{total} hotspots for classification")

    print(f"🎉 Batch classification completed in {time.time() - start_time:.1f}s")

if __name__ == '__main__':
    batch_classify_all()
