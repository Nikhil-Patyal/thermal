import os
import django
import pandas as pd
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from hotspots.models import Hotspot
from ml.feature_engineering import FeatureExtractor
from ml.evidence_engine import EvidenceEngine

def run():
    print("Fetching Indian hotspots...")
    hotspots = list(Hotspot.objects.filter(
        latitude__gte=6, latitude__lte=36,
        longitude__gte=68, longitude__lte=98,
        latitude__isnull=False, longitude__isnull=False
    ))
    print(f"Reclassifying {len(hotspots)} hotspots...")
    
    if not hotspots: return
    
    extractor = FeatureExtractor()
    engine = EvidenceEngine()
    
    X_df = extractor.extract_features(hotspots, fit_dbscan=False)
    results_df = engine.generate_weak_labels(X_df)
    
    for i, hotspot in enumerate(hotspots):
        if hotspot.id not in results_df.index:
            continue
            
        res = results_df.loc[hotspot.id]
        hotspot.predicted_class = res['label']
        hotspot.source_type = res['label']
        hotspot.processing_status = 'COMPLETED'
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

    Hotspot.objects.bulk_update(
        hotspots,
        ['predicted_class', 'source_type', 'processing_status', 'confidence_score', 'shap_values'],
        batch_size=200,
    )
    print("Done classifying India.")

run()
