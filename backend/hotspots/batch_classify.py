"""
Batch classification module — runs LightGBM and IsolationForest on all hotspots in bulk.
All enrichment must be completed before calling this module.
"""
import os
import time
import joblib
import numpy as np
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from hotspots.models import Hotspot
from ml.feature_engineering import FeatureExtractor

# Map class index to human readable name – keep in sync with models
CLASS_MAP = {
    0: 'Wildfire',
    1: 'Industrial Fire / Gas Flare',
    2: 'Agriculture Burning',
    3: 'Mining Activity / Persistent',
    -1: 'Unknown / Uncertain',
}

def batch_classify_all(chunk_size=500):
    """Classify all hotspots in bulk, updating the DB via bulk_update.

    Assumes that all enrichment fields (weather, air_quality, etc.) are present.
    """
    total = Hotspot.objects.count()
    if total == 0:
        print("✅ No hotspots to classify.")
        return

    # Load models once
    ml_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml')
    lgb_path = os.path.join(ml_dir, 'lightgbm_model.pkl')
    iso_path = os.path.join(ml_dir, 'iso_forest.pkl')

    lgb_model = None
    iso_model = None
    if os.path.exists(lgb_path):
        lgb_model = joblib.load(lgb_path)
        print("✅ Loaded LightGBM model")
    else:
        print("⚠️ LightGBM model not found at", lgb_path)

    if os.path.exists(iso_path):
        iso_model = joblib.load(iso_path)
        print("✅ Loaded IsolationForest model")
    else:
        print("⚠️ IsolationForest model not found at", iso_path)

    extractor = FeatureExtractor()
    processed = 0
    start_time = time.time()

    while processed < total:
        # Load a chunk of hotspots (including related foreign keys for feature extraction)
        hotspots_qs = Hotspot.objects.all().order_by('id')[processed:processed + chunk_size]
        hotspots = list(hotspots_qs)
        if not hotspots:
            break

        # Feature extraction – fit_dbscan only on first chunk (others already have DBSCAN info)
        X_df = extractor.extract_features(hotspots, fit_dbscan=False)
        if X_df.empty:
            print("⚠️ Feature extraction returned empty DataFrame for chunk starting at", processed)
            processed += len(hotspots)
            continue

        # Drop non‑model columns
        drop_cols = [c for c in ['lat', 'lng', 'cluster_id', 'id'] if c in X_df.columns]
        X_features = X_df.drop(columns=drop_cols)
        X_features = X_features.fillna(-999)

        # Predict class & confidence
        if lgb_model:
            class_idx = lgb_model.predict(X_features)
            class_probs = lgb_model.predict_proba(X_features)
            # Smooth probabilities to prevent 100% confidence in UI
            class_probs = np.clip(class_probs * 0.98 + 0.01, 0, 0.99)
        else:
            class_idx = np.full(len(X_features), -1)
            class_probs = np.zeros((len(X_features), len(CLASS_MAP)))

        # Optional anomaly score from IsolationForest
        anomaly_scores = None
        if iso_model:
            anomaly_scores = iso_model.score_samples(X_features)

        # Prepare objects for bulk_update
        for i, hotspot in enumerate(hotspots):
            hid = hotspot.id
            if hid not in X_df.index:
                continue
            idx = X_df.index.get_loc(hid)
            pred_idx = class_idx[idx]
            pred_name = CLASS_MAP.get(int(pred_idx), 'Unknown / Uncertain')
            prob = max(class_probs[idx]) if class_probs is not None else 0.0
            hotspot.predicted_class = pred_name
            hotspot.confidence_score = float(prob)
            # Store SHAP‑like payload – limited to key evidence here
            evidence = {
                'frp': X_features.iloc[idx].get('frp'),
                'brightness': X_features.iloc[idx].get('brightness'),
                'population_density': X_features.iloc[idx].get('pop_count'),
                'gdp': X_features.iloc[idx].get('gdp'),
                'anomaly_score': float(anomaly_scores[idx]) if anomaly_scores is not None else None,
            }
            hotspot.shap_values = evidence

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
