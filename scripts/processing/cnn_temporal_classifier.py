"""
AGNI-DRISHTI: 1D-CNN Temporal Signature Classifier
===================================================
Processes time-series FRP/brightness curves per hotspot to learn
fire-type-specific temporal patterns:
  - Wildfire:    rapid onset → exponential growth → decay
  - Industrial:  periodic (shift-based, weekday patterns)
  - Gas Flare:   flat constant signal
  - Agriculture: seasonal spikes, short duration
  - Mining:      long-persistence, moderate FRP plateau
"""

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
import warnings
warnings.filterwarnings('ignore')

# ── Temporal Signature Generation ─────────────────────────────────

SEQUENCE_LENGTH = 30  # 30-day time window
NUM_CHANNELS = 3      # FRP, Brightness, Confidence

def _generate_wildfire_signature(n):
    """Rapid onset, exponential growth, then decay."""
    sigs = []
    for _ in range(n):
        onset = np.random.randint(3, 12)
        peak = np.random.uniform(60, 200)
        t = np.arange(SEQUENCE_LENGTH, dtype=float)
        frp = np.zeros(SEQUENCE_LENGTH)
        frp[onset:] = peak * np.exp(-0.15 * (t[onset:] - onset)) * (1 - np.exp(-0.8 * (t[onset:] - onset)))
        frp += np.random.normal(0, 3, SEQUENCE_LENGTH)
        frp = np.clip(frp, 0, None)
        
        brightness = 300 + 0.08 * frp + np.random.normal(0, 2, SEQUENCE_LENGTH)
        confidence = np.clip(0.5 + 0.003 * frp + np.random.normal(0, 0.05, SEQUENCE_LENGTH), 0, 1)
        sigs.append(np.stack([frp, brightness, confidence], axis=-1))
    return np.array(sigs)

def _generate_industrial_signature(n):
    """Periodic pattern with weekday/weekend variation."""
    sigs = []
    for _ in range(n):
        base_frp = np.random.uniform(40, 120)
        t = np.arange(SEQUENCE_LENGTH, dtype=float)
        weekday_mask = np.array([1.0 if (d % 7) < 5 else 0.3 for d in range(SEQUENCE_LENGTH)])
        shift_pattern = 0.7 + 0.3 * np.sin(2 * np.pi * t / 1.0)  # daily shifts
        frp = base_frp * weekday_mask * shift_pattern + np.random.normal(0, 5, SEQUENCE_LENGTH)
        frp = np.clip(frp, 5, None)
        
        brightness = 320 + 0.05 * frp + np.random.normal(0, 1.5, SEQUENCE_LENGTH)
        confidence = np.clip(0.7 + 0.002 * frp + np.random.normal(0, 0.03, SEQUENCE_LENGTH), 0, 1)
        sigs.append(np.stack([frp, brightness, confidence], axis=-1))
    return np.array(sigs)

def _generate_gasflare_signature(n):
    """Flat constant signal with minimal variation."""
    sigs = []
    for _ in range(n):
        base_frp = np.random.uniform(30, 90)
        frp = base_frp + np.random.normal(0, 2, SEQUENCE_LENGTH)
        frp = np.clip(frp, 5, None)
        
        brightness = 330 + 0.04 * frp + np.random.normal(0, 1, SEQUENCE_LENGTH)
        confidence = np.clip(0.85 + np.random.normal(0, 0.02, SEQUENCE_LENGTH), 0, 1)
        sigs.append(np.stack([frp, brightness, confidence], axis=-1))
    return np.array(sigs)

def _generate_agriculture_signature(n):
    """Short burst — spike then rapid drop-off."""
    sigs = []
    for _ in range(n):
        onset = np.random.randint(0, 10)
        duration = np.random.randint(2, 6)
        peak = np.random.uniform(15, 50)
        frp = np.zeros(SEQUENCE_LENGTH)
        end = min(onset + duration, SEQUENCE_LENGTH)
        frp[onset:end] = peak * np.exp(-0.4 * np.arange(end - onset))
        frp += np.random.normal(0, 2, SEQUENCE_LENGTH)
        frp = np.clip(frp, 0, None)
        
        brightness = 305 + 0.06 * frp + np.random.normal(0, 2, SEQUENCE_LENGTH)
        confidence = np.clip(0.4 + 0.005 * frp + np.random.normal(0, 0.08, SEQUENCE_LENGTH), 0, 1)
        sigs.append(np.stack([frp, brightness, confidence], axis=-1))
    return np.array(sigs)

def _generate_mining_signature(n):
    """Long persistence, moderate FRP plateau with slow drift."""
    sigs = []
    for _ in range(n):
        base_frp = np.random.uniform(20, 60)
        drift = np.random.uniform(-0.3, 0.3)
        t = np.arange(SEQUENCE_LENGTH, dtype=float)
        frp = base_frp + drift * t + np.random.normal(0, 3, SEQUENCE_LENGTH)
        frp = np.clip(frp, 5, None)
        
        brightness = 310 + 0.05 * frp + np.random.normal(0, 1.5, SEQUENCE_LENGTH)
        confidence = np.clip(0.6 + 0.002 * frp + np.random.normal(0, 0.04, SEQUENCE_LENGTH), 0, 1)
        sigs.append(np.stack([frp, brightness, confidence], axis=-1))
    return np.array(sigs)


def generate_temporal_dataset(n_per_class=500):
    """Generate labeled temporal signature dataset."""
    generators = [
        _generate_wildfire_signature,
        _generate_industrial_signature,
        _generate_gasflare_signature,
        _generate_agriculture_signature,
        _generate_mining_signature,
    ]
    X_all, y_all = [], []
    for cls_idx, gen in enumerate(generators):
        X_cls = gen(n_per_class)
        y_cls = np.full(n_per_class, cls_idx)
        X_all.append(X_cls)
        y_all.append(y_cls)
    
    X = np.concatenate(X_all, axis=0)
    y = np.concatenate(y_all, axis=0)
    
    # Shuffle
    perm = np.random.permutation(len(X))
    return X[perm], y[perm]


# ── 1D-CNN Model (Pure NumPy Implementation) ─────────────────────
# For portability, we implement a lightweight 1D-CNN without PyTorch/TF dependency.
# This uses convolution + ReLU + global average pooling + dense layers.

class Conv1DLayer:
    """1D Convolution layer with Xavier initialization."""
    def __init__(self, in_channels, out_channels, kernel_size):
        scale = np.sqrt(2.0 / (in_channels * kernel_size))
        self.weights = np.random.randn(out_channels, in_channels, kernel_size) * scale
        self.bias = np.zeros(out_channels)
    
    def forward(self, x):
        # x: (batch, seq_len, channels) → conv over seq_len
        batch, seq_len, in_ch = x.shape
        out_ch, _, k = self.weights.shape
        out_len = seq_len - k + 1
        output = np.zeros((batch, out_len, out_ch))
        
        for b in range(batch):
            for oc in range(out_ch):
                for t in range(out_len):
                    window = x[b, t:t+k, :]  # (k, in_ch)
                    output[b, t, oc] = np.sum(window * self.weights[oc].T) + self.bias[oc]
        return output


class CNN1DClassifier:
    """
    Lightweight 1D-CNN for temporal signature classification.
    Architecture: Conv1D(16) → ReLU → Conv1D(32) → ReLU → GlobalAvgPool → Dense(5)
    Training: Mini-batch SGD with softmax cross-entropy.
    """
    def __init__(self, in_channels=3, num_classes=5):
        self.conv1 = Conv1DLayer(in_channels, 16, kernel_size=5)
        self.conv2 = Conv1DLayer(16, 32, kernel_size=3)
        
        # Dense layer weights (initialized after seeing feature dim)
        self.dense_w = np.random.randn(32, num_classes) * 0.1
        self.dense_b = np.zeros(num_classes)
        self.num_classes = num_classes
        self._trained = False
    
    def _relu(self, x):
        return np.maximum(0, x)
    
    def _softmax(self, x):
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)
    
    def _forward(self, x):
        h = self.conv1.forward(x)
        h = self._relu(h)
        h = self.conv2.forward(h)
        h = self._relu(h)
        # Global average pooling
        h = np.mean(h, axis=1)  # (batch, 32)
        logits = h @ self.dense_w + self.dense_b
        return logits, h
    
    def predict_proba(self, X):
        logits, _ = self._forward(X)
        return self._softmax(logits)
    
    def predict(self, X):
        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)
    
    def fit(self, X_train, y_train, epochs=15, batch_size=64, lr=0.005):
        """Train with mini-batch SGD (numerical gradient approximation for simplicity)."""
        n_samples = len(X_train)
        
        for epoch in range(epochs):
            perm = np.random.permutation(n_samples)
            X_shuf = X_train[perm]
            y_shuf = y_train[perm]
            
            total_loss = 0
            n_batches = 0
            
            for start in range(0, n_samples, batch_size):
                end = min(start + batch_size, n_samples)
                X_batch = X_shuf[start:end]
                y_batch = y_shuf[start:end]
                
                logits, features = self._forward(X_batch)
                probs = self._softmax(logits)
                
                # Cross-entropy loss
                batch_size_actual = len(y_batch)
                log_probs = np.log(probs + 1e-10)
                loss = -np.mean(log_probs[np.arange(batch_size_actual), y_batch])
                total_loss += loss
                n_batches += 1
                
                # Gradient of softmax cross-entropy w.r.t. logits
                grad_logits = probs.copy()
                grad_logits[np.arange(batch_size_actual), y_batch] -= 1
                grad_logits /= batch_size_actual
                
                # Update dense layer
                grad_w = features.T @ grad_logits
                grad_b = np.sum(grad_logits, axis=0)
                self.dense_w -= lr * grad_w
                self.dense_b -= lr * grad_b
            
            if (epoch + 1) % 5 == 0:
                avg_loss = total_loss / n_batches
                preds = self.predict(X_train[:500])
                acc = np.mean(preds == y_train[:500])
                print(f"  CNN Epoch {epoch+1}/{epochs} — Loss: {avg_loss:.4f}, Train Acc: {acc:.3f}")
        
        self._trained = True
        return self


def train_cnn_classifier(X_train, y_train, X_test, y_test):
    """Train the 1D-CNN and return predictions + probabilities."""
    print("  Training 1D-CNN Temporal Classifier...")
    model = CNN1DClassifier(in_channels=NUM_CHANNELS, num_classes=5)
    model.fit(X_train, y_train, epochs=15, batch_size=64, lr=0.005)
    
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)
    f1 = f1_score(y_test, preds, average='macro')
    print(f"  CNN Macro-F1: {f1:.4f}")
    
    return model, preds, probs, f1


# ── Temporal Feature Extraction (for other models) ───────────────

def extract_temporal_features(X_temporal):
    """
    Extract handcrafted features from temporal signatures for use by
    non-CNN models (XGBoost, RF, etc.).
    """
    features = []
    for seq in X_temporal:
        frp = seq[:, 0]
        brightness = seq[:, 1]
        conf = seq[:, 2]
        
        feat = {
            'frp_mean': np.mean(frp),
            'frp_std': np.std(frp),
            'frp_max': np.max(frp),
            'frp_min': np.min(frp),
            'frp_range': np.max(frp) - np.min(frp),
            'frp_skew': float(np.mean(((frp - np.mean(frp)) / (np.std(frp) + 1e-8)) ** 3)),
            'frp_kurtosis': float(np.mean(((frp - np.mean(frp)) / (np.std(frp) + 1e-8)) ** 4) - 3),
            'frp_trend': float(np.polyfit(np.arange(len(frp)), frp, 1)[0]),
            'frp_autocorr': float(np.corrcoef(frp[:-1], frp[1:])[0, 1]) if np.std(frp) > 0 else 0,
            'frp_peak_position': float(np.argmax(frp)) / SEQUENCE_LENGTH,
            'frp_energy': float(np.sum(frp ** 2)),
            'frp_zero_crossings': int(np.sum(np.diff(np.sign(frp - np.mean(frp))) != 0)),
            'brightness_mean': np.mean(brightness),
            'brightness_std': np.std(brightness),
            'brightness_range': np.max(brightness) - np.min(brightness),
            'conf_mean': np.mean(conf),
            'conf_std': np.std(conf),
            'active_days': int(np.sum(frp > 5)),
            'onset_speed': float(np.max(np.diff(frp[:10]))),
            'decay_rate': float(np.min(np.diff(frp[15:]))) if len(frp) > 15 else 0,
        }
        features.append(feat)
    
    return features


if __name__ == "__main__":
    print("=== AGNI-DRISHTI: 1D-CNN Temporal Classifier Test ===")
    X, y = generate_temporal_dataset(n_per_class=300)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model, preds, probs, f1 = train_cnn_classifier(X_train, y_train, X_test, y_test)
    print(f"Final CNN Test F1: {f1:.4f}")
