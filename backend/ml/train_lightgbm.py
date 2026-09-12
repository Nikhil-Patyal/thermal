import os
import django
import sys
import numpy as np
import pandas as pd
import lightgbm as lgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score
from sklearn.ensemble import IsolationForest

# Setup Django env
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from hotspots.models import Hotspot
from ml.evidence_engine import EvidenceEngine
from ml.feature_engineering import FeatureExtractor
from sklearn.model_selection import GroupKFold

CLASS_MAP = {
    0: 'Wildfire',
    1: 'Industrial Fire / Gas Flare',
    2: 'Agriculture Burning',
    3: 'Mining Activity / Persistent',
    -1: 'Unknown / Uncertain'
}

def train_models():
    print("Fetching authentic Hotspot data from DB...")
    # Fetch 5000 recent fully-enriched hotspots
    hotspots = Hotspot.objects.select_related(
        'weather', 'population_exposure', 'economic_exposure'
    ).order_by('-acquisition_date')[:5000]
    
    print(f"Loaded {len(hotspots)} records.")
    if len(hotspots) < 100:
        print("Not enough authentic data to train. Ingest more data via tasks.")
        return
        
    print("Extracting features (DBSCAN + Temporal + Spatial)...")
    extractor = FeatureExtractor()
    X_df = extractor.extract_features(hotspots, fit_dbscan=True)
    
    # 4. Generate Weak Labels using Evidence Engine
    print("Generating Weak Labels via Evidence Engine...")
    engine = EvidenceEngine()
    labels_df = engine.generate_weak_labels(X_df)
    
    # Drop lat/lng to avoid overfitting to exact locations
    X_features = X_df.drop(columns=['lat', 'lng', 'cluster_id'])
    y = labels_df['label_idx'].values
    groups = X_df['cluster_id'].values  # Used for spatial splitting
    
    print("Training Isolation Forest (Anomaly Detection)...")
    # Impute NaNs strictly with a zero-state equivalent or median for IsolationForest,
    # because IF doesn't support NaNs natively unlike LightGBM.
    X_features_imputed = X_features.fillna(-999)
    iso_forest = IsolationForest(contamination=0.05, random_state=42)
    iso_forest.fit(X_features_imputed)
    
    # Check if we have any valid labeled data (target != -1)
    valid_labels_mask = y != -1
    X_valid = X_features[valid_labels_mask]
    y_valid = y[valid_labels_mask]
    groups_valid = groups[valid_labels_mask]
    
    lgb_model = None
    if len(y_valid) > 10:
        print(f"Splitting authentic data (Train/Test) with {len(y_valid)} labeled samples using GroupKFold...")
        
        # Ensure spatial isolation (leakage-proof)
        gkf = GroupKFold(n_splits=5)
        train_idx, test_idx = next(gkf.split(X_valid, y_valid, groups=groups_valid))
        
        X_train, X_test = X_valid.iloc[train_idx], X_valid.iloc[test_idx]
        y_train, y_test = y_valid[train_idx], y_valid[test_idx]
        
        print("Training LightGBM Classifier...")
        params = {
            'objective': 'multiclass',
            'num_class': 4,
            'metric': 'multi_logloss',
            'verbosity': -1,
            'learning_rate': 0.05,
            'num_leaves': 31,
            'random_state': 42
        }
        
        lgb_model = lgb.LGBMClassifier(**params, n_estimators=150)
        lgb_model.fit(X_train, y_train)
        
        print("Evaluating Model on Test Set...")
        preds = lgb_model.predict(X_test)
        f1 = f1_score(y_test, preds, average='macro')
        print(f"Macro F1 Score: {f1:.4f}")
        
        print("\nClassification Report:")
        report_labels = [CLASS_MAP[i] for i in sorted(list(set(y_test)))]
        print(classification_report(y_test, preds, target_names=report_labels))
    else:
        print("⚠️ No authentically labeled data available (all targets are -1 / Unknown).")
        print("Skipping LightGBM supervised training.")
    
    # Save models
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    iso_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'iso_forest.pkl')
    joblib.dump(iso_forest, iso_path)
    
    if lgb_model:
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lightgbm_model.pkl')
        joblib.dump(lgb_model, model_path)
    
    print(f"Models saved successfully to {os.path.dirname(os.path.abspath(__file__))}")

if __name__ == "__main__":
    train_models()
