import os
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression

class MetaLearner:
    """
    Ensemble meta-learner that combines predictions from multiple base models
    (LightGBM, XGBoost, CatBoost).
    """
    def __init__(self, model_dir='ml/models'):
        self.model_dir = model_dir
        self.meta_model_path = os.path.join(model_dir, 'meta_learner.pkl')
        self.meta_model = None

    def fit(self, base_preds, y):
        """
        base_preds: array-like of shape (n_samples, n_classes * n_models)
        y: array-like of shape (n_samples,)
        """
        self.meta_model = LogisticRegression(max_iter=1000, multi_class='multinomial')
        self.meta_model.fit(base_preds, y)
        
        os.makedirs(self.model_dir, exist_ok=True)
        joblib.dump(self.meta_model, self.meta_model_path)
        return self

    def load(self):
        if os.path.exists(self.meta_model_path):
            self.meta_model = joblib.load(self.meta_model_path)
        else:
            raise FileNotFoundError(f"Meta learner not found at {self.meta_model_path}")

    def predict_proba(self, base_preds):
        if self.meta_model is None:
            self.load()
        return self.meta_model.predict_proba(base_preds)
        
    def predict(self, base_preds):
        if self.meta_model is None:
            self.load()
        return self.meta_model.predict(base_preds)
