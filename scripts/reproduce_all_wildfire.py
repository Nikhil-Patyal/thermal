import os
import django
import sys
import numpy as np

# Set up Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotspots.models import Hotspot
from ml.feature_engineering import FeatureExtractor

def fallback_classification(features: dict) -> tuple[str, float]:
    # Aggregate across radii (keys end with 'm')
    forest_sum = sum(v for k, v in features.items() if k.startswith('forest_fraction') and v is not None)
    cropland_sum = sum(v for k, v in features.items() if k.startswith('cropland_fraction') and v is not None)
    builtup_sum = sum(v for k, v in features.items() if k.startswith('builtup_fraction') and v is not None)
    industrial_sum = sum(v for k, v in features.items() if k.startswith('industrial_count') and v is not None)

    # Simple scoring heuristic
    scores = {
        'Wildfire': forest_sum,
        'Industrial Fire / Gas Flare': industrial_sum,
        'Agriculture Burning': cropland_sum,
    }
    total = sum(scores.values())
    if total == 0:
        return ('Unknown / Uncertain', 0.0)
    # Determine best class
    best_class, best_score = max(scores.items(), key=lambda item: item[1])
    confidence = best_score / total
    # Apply configurable threshold
    try:
        threshold = float(os.getenv('FALLBACK_CONFIDENCE_THRESHOLD', '0.4'))
    except Exception:
        threshold = 0.4
    if confidence >= threshold:
        return (best_class, confidence)
    else:
        return ('Unknown / Uncertain', confidence)

def analyze_fallbacks():
    print("--- Reproducing 'all-wildfire/100%' behavior ---\n")
    
    hotspots = Hotspot.objects.exclude(latitude__isnull=True).order_by('-id')[:10]
    
    if not hotspots:
        print("No hotspots found in the database.")
        return
        
    print(f"Loaded {len(hotspots)} hotspots for testing.")
    
    extractor = FeatureExtractor()
    X_df = extractor.extract_features(list(hotspots), fit_dbscan=False)
    
    for h in hotspots:
        if h.id not in X_df.index:
            continue
            
        features = X_df.loc[h.id].to_dict()
        
        pred_name, prob = fallback_classification(features)
        
        smoothed_prob = np.clip(prob * 0.98 + 0.01, 0, 0.99)
        
        forest_sum = sum(v for k, v in features.items() if k.startswith('forest_fraction') and v is not None)
        cropland_sum = sum(v for k, v in features.items() if k.startswith('cropland_fraction') and v is not None)
        builtup_sum = sum(v for k, v in features.items() if k.startswith('builtup_fraction') and v is not None)
        industrial_sum = sum(v for k, v in features.items() if k.startswith('industrial_count') and v is not None)
        
        print(f"Hotspot {h.id} at {h.latitude}, {h.longitude}:")
        print(f"  Geosums -> Forest: {forest_sum}, Crop: {cropland_sum}, Builtup: {builtup_sum}, Industrial: {industrial_sum}")
        print(f"  Fallback -> Class: {pred_name}, Prob: {prob:.4f}")
        print(f"  Smoothed Confidence (UI) -> {smoothed_prob:.4f} (~{smoothed_prob*100:.1f}%)")
        print("-" * 40)

if __name__ == '__main__':
    analyze_fallbacks()
