import pandas as pd
import numpy as np
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_curve
from sklearn.ensemble import RandomForestClassifier
import os
import joblib

def load_reviewed_data(csv_path):
    """
    Load independently human-reviewed dataset.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Labelled dataset not found at {csv_path}. Please run export_for_review and review data first.")
    
    df = pd.read_csv(csv_path)
    
    # Filter only records that have a reviewer_label
    df = df[df['reviewer_label'].notnull()]
    
    return df

def extract_features(df):
    """
    Extract relevant ML features.
    """
    features = [
        'frp', 'brightness', 'bright_t31', 'scan', 'track',
        'cropland_fraction', 'tree_fraction', 'shrub_fraction', 
        'grass_fraction', 'other_fraction'
    ]
    
    # Fill missing with 0 or a designated value (but they shouldn't be missing for valid data)
    X = df[features].fillna(0)
    
    # Target encoding
    # Map classes to binary or multiclass
    # We expect reviewer_label to be e.g., 'agriculture', 'wildland'
    y = df['reviewer_label'].map({
        'agriculture': 1,
        'wildland': 0
    }).fillna(-1) # Filter out -1 later
    
    # Simple geographic grouping to avoid spatial leakage
    # Rounding coordinates to 0.5 degrees creates roughly 50km blocks
    groups = df['latitude'].round(1).astype(str) + "_" + df['longitude'].round(1).astype(str)
    
    return X, y, groups

def train_and_evaluate(csv_path):
    """
    Train and evaluate the model using grouped spatial holdouts.
    """
    df = load_reviewed_data(csv_path)
    if len(df) < 100:
        print("Warning: Dataset is too small (<100 samples) for reliable evaluation.")
        
    X, y, groups = extract_features(df)
    
    # Filter valid targets only
    valid_idx = y != -1
    X = X[valid_idx]
    y = y[valid_idx]
    groups = groups[valid_idx]
    
    if len(X) == 0:
        raise ValueError("No valid labels found for agriculture/wildland.")
    
    # Spatial Holdout Split (to prevent spatial leakage)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups))
    
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    
    print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples (Spatial Holdout).")
    
    # Simple Baseline comparison would go here.
    
    # Train Random Forest
    rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    rf.fit(X_train, y_train)
    
    # Evaluate
    y_probs = rf.predict_proba(X_test)[:, 1]
    
    print("\n--- Model Evaluation (Test Split) ---")
    print("\nSelecting coverage based on error trade-offs:")
    
    # Evaluate at multiple thresholds
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    for thresh in thresholds:
        y_pred = (y_probs >= thresh).astype(int)
        
        # Calculate coverage (what % of test set exceeded threshold)
        # Assuming probability >= thresh OR <= (1-thresh) triggers a classification
        covered = (y_probs >= thresh) | (y_probs <= (1-thresh))
        coverage = covered.mean() * 100
        
        print(f"\nThreshold: {thresh}")
        print(f"Classification Coverage: {coverage:.1f}%")
        
        if coverage > 0:
            # Evaluate only on covered samples
            y_test_covered = y_test[covered]
            y_pred_covered = y_pred[covered]
            print("Classification Report on Covered Set:")
            print(classification_report(y_test_covered, y_pred_covered, target_names=['wildland', 'agriculture']))
            print("Confusion Matrix:")
            print(confusion_matrix(y_test_covered, y_pred_covered))
            
    # Save the model
    os.makedirs('models', exist_ok=True)
    model_path = 'models/rf_mixed_landscape.pkl'
    joblib.dump(rf, model_path)
    print(f"\nModel saved to {model_path}")
    print("\nIMPORTANT: Ensure a user-approved acceptable error criterion is met before deploying this model to production.")

if __name__ == '__main__':
    try:
        train_and_evaluate('review_export.csv')
    except Exception as e:
        print(f"Pipeline blocked: {e}")
