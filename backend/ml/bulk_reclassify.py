import os
import django
import sys
import joblib
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotspots.models import Hotspot
from ml.feature_engineering import FeatureExtractor
from ml.meta_learner import MetaLearner

CLASS_MAP = {
    0: 'Wildfire',
    1: 'Industrial Fire / Gas Flare',
    2: 'Agriculture Burning',
    3: 'Mining Activity / Persistent',
    -1: 'Unknown / Uncertain'
}

def run_bulk_reclassification():
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
    
    print("Loading models from:", model_dir)
    m1 = joblib.load(os.path.join(model_dir, 'base_lgbm1.pkl'))
    m2 = joblib.load(os.path.join(model_dir, 'base_lgbm2.pkl'))
    m3 = joblib.load(os.path.join(model_dir, 'base_rf.pkl'))
    
    meta = MetaLearner(model_dir=model_dir)
    meta.load()
    
    chunk_size = 500
    total = Hotspot.objects.count()
    
    print(f"Starting bulk reclassification of {total} hotspots via Ensemble ML...")
    
    for offset in range(0, total, chunk_size):
        print(f"Processing chunk {offset} to {offset+chunk_size}...")
        hotspots = list(Hotspot.objects.order_by('id')[offset:offset+chunk_size])
        if not hotspots:
            break
            
        extractor = FeatureExtractor()
        X_df = extractor.extract_features(hotspots, fit_dbscan=True)
        
        cols_to_drop = ['lat', 'lng', 'cluster_id', 'id']
        target_features = X_df.drop(columns=[c for c in cols_to_drop if c in X_df.columns])
        target_features = target_features.fillna(-999)
        
        # Predict base
        p1 = m1.predict_proba(target_features)
        p2 = m2.predict_proba(target_features)
        p3 = m3.predict_proba(target_features)
        
        meta_feat = np.hstack([p1, p2, p3])
        
        pred_class_idx = meta.predict(meta_feat)
        pred_probs = meta.predict_proba(meta_feat)
        
        for i, hotspot in enumerate(hotspots):
            if hotspot.id in target_features.index:
                idx = target_features.index.get_loc(hotspot.id)
                c_idx = pred_class_idx[idx]
                c_prob = max(pred_probs[idx])
                
                hotspot.predicted_class = CLASS_MAP.get(c_idx, 'Unknown / Uncertain')
                hotspot.confidence_score = float(c_prob)
                
        Hotspot.objects.bulk_update(hotspots, ['predicted_class', 'confidence_score'])
        print(f"Updated chunk {offset} to {offset+chunk_size}")

if __name__ == '__main__':
    run_bulk_reclassification()
