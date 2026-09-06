import os
import django
import sys
import numpy as np
import pandas as pd
import lightgbm as lgb
import optuna
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score

# Setup Django env
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from hotspots.models import Hotspot

def load_data():
    """
    Simulate loading data and generating weak-supervision labels.
    """
    # In a real scenario we would fetch Hotspots from DB with enrichment features.
    # We will generate some dummy data for the purpose of the 1-day sprint.
    np.random.seed(42)
    n_samples = 1000
    
    features = pd.DataFrame({
        'frp': np.random.uniform(5, 500, n_samples),
        'brightness': np.random.uniform(280, 400, n_samples),
        'distance_to_industry': np.random.uniform(0.1, 20.0, n_samples),
        'pm25': np.random.uniform(10, 200, n_samples),
        'temperature_c': np.random.uniform(10, 45, n_samples),
        'population_count': np.random.randint(100, 100000, n_samples)
    })
    
    # Weak supervision rules (simplified mock)
    labels = []
    classes = ['industrial fire', 'gas flare', 'agricultural burn', 'mining activity', 'wildfire', 'other persistent source', 'unknown']
    
    for i in range(n_samples):
        if features['distance_to_industry'][i] < 2.0 and features['frp'][i] > 100:
            labels.append(0) # industrial fire
        elif features['distance_to_industry'][i] < 1.0 and features['brightness'][i] > 350:
            labels.append(1) # gas flare
        elif features['temperature_c'][i] > 35 and features['population_count'][i] < 5000:
            labels.append(4) # wildfire
        else:
            labels.append(np.random.randint(0, 7))
            
    return features, np.array(labels)

def objective(trial, X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    param = {
        'objective': 'multiclass',
        'num_class': 7,
        'metric': 'multi_logloss',
        'verbosity': -1,
        'boosting_type': 'gbdt',
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
        'num_leaves': trial.suggest_int('num_leaves', 20, 150),
        'max_depth': trial.suggest_int('max_depth', 3, 12),
        'min_child_samples': trial.suggest_int('min_child_samples', 5, 50)
    }
    
    gbm = lgb.LGBMClassifier(**param, n_estimators=100)
    gbm.fit(X_train, y_train)
    preds = gbm.predict(X_test)
    
    return f1_score(y_test, preds, average='macro')

def train_model():
    print("Loading data & generating weak labels...")
    X, y = load_data()
    
    print("Starting Optuna hyperparameter optimization...")
    study = optuna.create_study(direction='maximize')
    study.optimize(lambda trial: objective(trial, X, y), n_trials=10) # 10 trials for speed
    
    print("Best params:", study.best_params)
    print("Best Macro F1:", study.best_value)
    
    print("Training final model on full dataset...")
    best_params = study.best_params
    best_params.update({'objective': 'multiclass', 'num_class': 7})
    
    final_model = lgb.LGBMClassifier(**best_params, n_estimators=200)
    final_model.fit(X, y)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lightgbm_model.pkl')
    joblib.dump(final_model, model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_model()
