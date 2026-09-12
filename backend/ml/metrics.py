import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any

import django

# Ensure Django is set up when this module is imported directly (e.g., during script execution)
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

from hotspots.models import Hotspot
from ml.feature_engineering import FeatureExtractor
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
)

# Path for the validation CSV – placed next to this module for easy access
VALIDATION_CSV = Path(__file__).resolve().parent / "validation_set.csv"


def generate_validation_set(max_rows: int = 200) -> pd.DataFrame:
    """Create a validation CSV from existing hotspots.

    The function pulls up to ``max_rows`` hotspots that already have a ground‑truth label
    (the ``label`` field is expected to be populated manually). All feature columns required
    by ``EvidenceEngine`` are extracted via ``FeatureExtractor`` and a ``true_label`` column
    is added. The resulting DataFrame is written to ``validation_set.csv`` and also
    returned for immediate use.
    """
    # Query hotspots that have a non‑null label (ground‑truth)
    qs = Hotspot.objects.filter(label__isnull=False).order_by("-acquisition_date")[:max_rows]
    if not qs:
        raise RuntimeError("No labelled hotspots found to build a validation set.")

    extractor = FeatureExtractor()
    # ``extract_features`` expects a list/queryset of Hotspot objects and returns a DataFrame
    feature_df = extractor.extract_features(qs, fit_dbscan=False)

    # Append the ground‑truth label from the model field
    true_labels = [hotspot.label for hotspot in qs]
    feature_df["true_label"] = true_labels

    # Persist to CSV – ensure deterministic column order for reproducibility
    feature_df.to_csv(VALIDATION_CSV, index=False)
    return feature_df


def load_validation_set() -> pd.DataFrame:
    """Load the validation set, generating it on‑the‑fly if the CSV is missing."""
    if not VALIDATION_CSV.exists():
        print("Validation CSV not found – generating from DB…")
        return generate_validation_set()
    return pd.read_csv(VALIDATION_CSV)


def compute_metrics(y_true, y_pred, class_map: Dict[int, str]) -> Dict[str, Any]:
    """Calculate common classification metrics.

    Parameters
    ----------
    y_true: array‑like of ground‑truth integer class IDs.
    y_pred: array‑like of predicted integer class IDs.
    class_map: mapping from integer IDs to human‑readable class names.
    """
    # Ensure inputs are numeric
    y_true = pd.Series(y_true).astype(int)
    y_pred = pd.Series(y_pred).astype(int)

    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    recall = recall_score(y_true, y_pred, average="weighted", zero_division=0)
    f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)

    # Classification report returns a dict keyed by class label (as string)
    report = classification_report(
        y_true,
        y_pred,
        target_names=[class_map.get(cls, str(cls)) for cls in sorted(class_map)],
        output_dict=True,
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "report": report,
    }
