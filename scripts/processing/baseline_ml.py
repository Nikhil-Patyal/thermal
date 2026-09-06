import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import xgboost as xgb
from sklearn.metrics import classification_report, f1_score
import shap

# Example Baseline Script for AGNI-DRISHTI 
# To be presented for SIH 26162

def create_mock_data(n_samples=1000):
    """
    Creates mock FIRMS + Temporal data for the baseline model.
    In production, this is queried from the PostGIS database.
    """
    np.random.seed(42)
    
    # Features: frp, brightness, persistence (days active), anomaly_ratio
    # Target: 0 (Wildfire), 1 (Industrial Fire), 2 (Gas Flare)
    
    data = {
        'frp': np.random.exponential(scale=30, size=n_samples),
        'brightness': np.random.normal(loc=310, scale=15, size=n_samples),
        'persistence_days': np.random.randint(1, 100, size=n_samples),
        'anomaly_ratio': np.random.uniform(0.5, 5.0, size=n_samples),
        'target': np.random.choice([0, 1, 2], size=n_samples, p=[0.5, 0.3, 0.2])
    }
    
    # Introduce some logic so the model can learn
    # Industrial fires (1) tend to have higher FRP and Anomaly Ratio
    mask_ind = data['target'] == 1
    data['frp'][mask_ind] += 50
    data['anomaly_ratio'][mask_ind] += 2.0
    
    # Gas Flares (2) tend to have high persistence
    mask_flare = data['target'] == 2
    data['persistence_days'][mask_flare] = np.random.randint(200, 365, size=np.sum(mask_flare))
    
    return pd.DataFrame(data)

def train_baseline():
    print("--- AGNI-DRISHTI Baseline ML Training ---")
    df = create_mock_data()
    
    X = df[['frp', 'brightness', 'persistence_days', 'anomaly_ratio']]
    y = df['target']
    
    # Level 1 Validation: Random Split (Note: We use Level 3-5 in production)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training XGBoost Classifier...")
    model = xgb.XGBClassifier(
        objective='multi:softprob',
        num_class=3,
        eval_metric='mlogloss',
        use_label_encoder=False
    )
    
    model.fit(X_train, y_train)
    
    print("\n--- Evaluation ---")
    preds = model.predict(X_test)
    print(classification_report(y_test, preds, target_names=['Wildfire', 'Industrial Fire', 'Gas Flare']))
    
    macro_f1 = f1_score(y_test, preds, average='macro')
    print(f"Macro-F1 Score: {macro_f1:.4f}")
    
    print("\n--- SHAP Explainability Demo ---")
    # Using TreeExplainer for XGBoost
    explainer = shap.TreeExplainer(model)
    # Generate SHAP values for a single test instance
    sample = X_test.iloc[[0]]
    shap_values = explainer.shap_values(sample)
    
    print(f"Sample Features:\n{sample.iloc[0]}")
    print(f"Predicted Class: {model.predict(sample)[0]}")
    print("SHAP values calculated successfully. Ready for visualization.")

if __name__ == "__main__":
    train_baseline()
