import os
import sys
import django
import numpy as np
import pandas as pd
import lightgbm as lgb
import joblib
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from hotspots.models import Hotspot
from ml.feature_engineering import FeatureExtractor
from ml.evidence_engine import EvidenceEngine
from ml.meta_learner import MetaLearner

CLASS_MAP = {
    0: 'Wildfire',
    1: 'Industrial Fire / Gas Flare',
    2: 'Agriculture Burning',
    3: 'Mining Activity / Persistent',
    -1: 'Unknown / Uncertain'
}

def evaluate_pipeline():
    print("Fetching historical hotspots for rigorous evaluation...")
    hotspots = Hotspot.objects.select_related(
        'weather', 'population_exposure', 'economic_exposure'
    ).order_by('-acquisition_date')[:1000]
    
    if len(hotspots) < 100:
        print("Not enough data.")
        return
        
    print("Extracting Features...")
    extractor = FeatureExtractor()
    X_df = extractor.extract_features(hotspots, fit_dbscan=True)
    
    print("Generating Weak Labels (Evidence Engine)...")
    engine = EvidenceEngine()
    labels_df = engine.generate_weak_labels(X_df)
    
    # Analyze Dataset
    total_obs = len(X_df)
    unknown_count = sum(labels_df['label'] == -1)
    weak_count = total_obs - unknown_count
    
    print(f"\n--- Data Quality Report ---")
    print(f"Total Authentic Observations: {total_obs}")
    print(f"Weakly Labeled Observations: {weak_count}")
    print(f"Unknown Observations: {unknown_count}")
    
    # Split Data
    cols_to_drop = ['lat', 'lng', 'cluster_id', 'id']
    X_features = X_df.drop(columns=[c for c in cols_to_drop if c in X_df.columns])
    y = labels_df['label'].values
    
    X_features = X_features.fillna(-999)
    
    valid_mask = y != -1
    if not valid_mask.any():
        print("No valid weak labels found.")
        return
        
    X_valid = X_features[valid_mask]
    y_valid = y[valid_mask]
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    train_idx, test_idx = next(skf.split(X_valid, y_valid))
    
    X_train, X_test = X_valid.iloc[train_idx], X_valid.iloc[test_idx]
    y_train, y_test = y_valid[train_idx], y_valid[test_idx]
    
    print("\nTraining Base Models...")
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
    os.makedirs(model_dir, exist_ok=True)
    
    # Model 1: LightGBM Default
    m1 = lgb.LGBMClassifier(objective='multiclass', num_class=4, random_state=42, n_estimators=100)
    m1.fit(X_train, y_train)
    joblib.dump(m1, os.path.join(model_dir, 'base_lgbm1.pkl'))
    
    # Model 2: LightGBM Different Hyperparams
    m2 = lgb.LGBMClassifier(objective='multiclass', num_class=4, random_state=123, n_estimators=150, learning_rate=0.05, num_leaves=15)
    m2.fit(X_train, y_train)
    joblib.dump(m2, os.path.join(model_dir, 'base_lgbm2.pkl'))
    
    # Model 3: Random Forest
    m3 = RandomForestClassifier(n_estimators=100, random_state=42)
    m3.fit(X_train, y_train)
    joblib.dump(m3, os.path.join(model_dir, 'base_rf.pkl'))
    
    print("\nTraining Meta-Learner...")
    preds1 = m1.predict_proba(X_train)
    preds2 = m2.predict_proba(X_train)
    preds3 = m3.predict_proba(X_train)
    
    meta_features_train = np.hstack([preds1, preds2, preds3])
    
    meta = MetaLearner(model_dir=model_dir)
    meta.fit(meta_features_train, y_train)
    
    print("\nEvaluating Ensemble...")
    t_preds1 = m1.predict_proba(X_test)
    t_preds2 = m2.predict_proba(X_test)
    t_preds3 = m3.predict_proba(X_test)
    meta_features_test = np.hstack([t_preds1, t_preds2, t_preds3])
    
    final_preds = meta.predict(meta_features_test)
    final_probs = meta.predict_proba(meta_features_test)
    
    print("\n--- Meta-Learner Performance ---")
    labels_present = sorted(list(set(y_test)))
    target_names = [CLASS_MAP[i] for i in labels_present if i in CLASS_MAP]
    
    report = classification_report(y_test, final_preds, target_names=target_names)
    print(report)
    
    cm = confusion_matrix(y_test, final_preds)
    print("Confusion Matrix:")
    print(cm)
    
if __name__ == "__main__":
    evaluate_pipeline()
