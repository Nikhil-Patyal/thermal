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
            hotspot.confidence_score = res.get('label_confidence_str')
            hotspot.attribution_status = res.get('attribution_status')
            hotspot.is_tentative = res.get('is_tentative', False)
            hotspot.evidence_strength = res.get('label_confidence_str')
            
            fractions = res.get('fractions')
            if fractions:
                hotspot.cropland_fraction = fractions.get('cropland_fraction')
                hotspot.tree_fraction = fractions.get('tree_fraction')
                hotspot.shrub_fraction = fractions.get('shrub_fraction')
                hotspot.grass_fraction = fractions.get('grass_fraction')
                hotspot.other_fraction = fractions.get('other_fraction')
                hotspot.valid_coverage = fractions.get('valid_coverage')
                hotspot.footprint_method = fractions.get('footprint_method')
                hotspot.landcover_source = fractions.get('landcover_source')
                hotspot.landcover_version = fractions.get('landcover_version')
            
            import math
            def clean_nans(obj):
                if isinstance(obj, dict):
                    return {k: clean_nans(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [clean_nans(v) for v in obj]
                elif isinstance(obj, float) and math.isnan(obj):
                    return None
                return obj
            
            output_payload = {
                "class": res['label'],
                "confidence_str": res.get('label_confidence_str'),
                "evidence": res.get('label_evidence', []),
                "features_used": [], 
                "data_sources": res.get('label_sources', []),
                "missing_sources": res.get('missing_sources', []),
                "fractions": fractions
            }
            hotspot.shap_values = clean_nans(output_payload)

        # Bulk update the fields we changed
        Hotspot.objects.bulk_update(
            hotspots,
            ['predicted_class', 'confidence_score', 'attribution_status', 'is_tentative', 'evidence_strength',
             'cropland_fraction', 'tree_fraction', 'shrub_fraction', 'grass_fraction', 'other_fraction',
             'valid_coverage', 'footprint_method', 'landcover_source', 'landcover_version', 'shap_values'],
            batch_size=chunk_size,
        )

        processed += len(hotspots)
        print(f"✅ Processed {processed}/{total} hotspots for classification")

    print(f"🎉 Batch classification completed in {time.time() - start_time:.1f}s")

if __name__ == '__main__':
    batch_classify_all()
