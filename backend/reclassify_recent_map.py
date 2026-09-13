import os
import time
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from hotspots.models import Hotspot
from ml.feature_engineering import FeatureExtractor
from ml.evidence_engine import EvidenceEngine

def reclassify_recent():
    print("Fetching the top 20,000 hotspots by FRP (visible on map)...")
    hotspots = list(Hotspot.objects.filter(latitude__isnull=False).order_by('-frp')[:20000])
    
    if not hotspots:
        print("No hotspots found.")
        return
        
    print(f"Reclassifying {len(hotspots)} hotspots using unified Overpass API...")
    
    extractor = FeatureExtractor()
    engine = EvidenceEngine()
    
    # Extract features (this will hit the new get_overpass_infrastructure_and_landcover)
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
    print("Done! Map will now reflect authentic data.")

if __name__ == '__main__':
    reclassify_recent()
