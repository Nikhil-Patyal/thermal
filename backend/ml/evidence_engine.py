import pandas as pd
import numpy as np
from .settings import WEIGHTS as SETTINGS_WEIGHTS

class EvidenceEngine:
    """
    Evaluates multiple independent signals to generate weak labels.
    Uses a scoring system combining FIRMS base features and geographic context.
    Produces class-wise scores, normalizes them to probabilities, and assigns 
    a label if confidence exceeds a threshold.
    """

    CLASS_MAP = {
        0: 'Wildfire',
        1: 'Industrial Fire / Gas Flare',
        2: 'Agriculture Burning',
        3: 'Mining Activity / Persistent',
        -1: 'Unknown / Uncertain'
    }

    EVIDENCE_THRESHOLD = 0.45  # Slightly lower to allow nuanced scores

    # Base weights defined in settings
    WEIGHTS = SETTINGS_WEIGHTS

    def generate_weak_labels(self, df):
        """
        Takes the feature dataframe and returns a DataFrame with:
        label, label_type, label_confidence, label_evidence (list), label_sources (list)
        """
        results = []
        
        for idx, row in df.iterrows():
            evidence = []
            sources = []
            missing = []
            # Separate score containers for land and other features
            land_scores = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0}
            other_scores = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0}

            # ---- Base FIRMS features (other) ----
            f = row.get('frp', np.nan)
            b = row.get('brightness', np.nan)
            day = row.get('is_day', np.nan)
            density = row.get('cluster_density', np.nan)

            if pd.notna(f) and f > 150 and pd.notna(b) and b > 330:
                other_scores[1] += self.WEIGHTS['extreme_heat']['weight']
                evidence.append("extreme_thermal_signature")
                sources.append("FIRMS")
            elif pd.notna(f) and f > 50:
                other_scores[0] += self.WEIGHTS['high_heat']['weight']
                evidence.append("high_thermal_signature")
                sources.append("FIRMS")

            if pd.notna(day) and day == 0.0:
                other_scores[3] += self.WEIGHTS['nighttime']['weight']
                evidence.append("nighttime_detection")
                sources.append("FIRMS_Temporal")
            elif pd.notna(day) and day == 1.0:
                other_scores[2] += self.WEIGHTS['daytime']['weight']
                evidence.append("daytime_detection")
                sources.append("FIRMS_Temporal")

            if pd.notna(density) and density >= 4:
                other_scores[0] += self.WEIGHTS['expanding_cluster']['weight']
                evidence.append("expanding_hotspot_cluster")
                sources.append("Spatial_DBSCAN")
            elif pd.notna(density) and density <= 2:
                other_scores[2] += self.WEIGHTS['isolated']['weight']
                evidence.append("isolated_detection")
                sources.append("Spatial_DBSCAN")

            # ---- Weather features (other) ----
            temp = row.get('temp_c', np.nan)
            humidity = row.get('humidity', np.nan)
            wind = row.get('wind_ms', np.nan)
            if pd.notna(temp):
                other_scores[0] += self.WEIGHTS.get('temp', {'weight': 0})['weight'] * (temp / 40.0)
                evidence.append(f"temp_{temp:.1f}")
                sources.append("OpenMeteo")
            if pd.notna(humidity):
                other_scores[2] += self.WEIGHTS.get('humidity', {'weight': 0})['weight'] * (humidity / 100.0)
                evidence.append(f"humidity_{humidity:.1f}")
                sources.append("OpenMeteo")
            if pd.notna(wind):
                other_scores[1] += self.WEIGHTS.get('wind', {'weight': 0})['weight'] * (wind / 15.0)
                evidence.append(f"wind_{wind:.1f}")
                sources.append("OpenMeteo")

            # ---- Socio‑economic features (other) ----
            pop = row.get('pop_count', np.nan)
            gdp = row.get('gdp', np.nan)
            if pd.notna(pop):
                other_scores[1] += self.WEIGHTS.get('population', {'weight': 0})['weight'] * (pop / 1e6)
                evidence.append(f"pop_{pop:.0f}")
                sources.append("WorldBank")
            if pd.notna(gdp):
                other_scores[1] += self.WEIGHTS.get('gdp', {'weight': 0})['weight'] * (gdp / 1e12)
                evidence.append(f"gdp_{gdp:.2e}")
                sources.append("WorldBank")

            # ---- Land‑cover features (land) ----
            forest = row.get('forest_fraction_1000m', np.nan)
            cropland = row.get('cropland_fraction_1000m', np.nan)
            industrial = row.get('industrial_count_1000m', np.nan)
            dist_industry = row.get('distance_to_industry', np.nan)
            if pd.notna(forest) and forest > 0.3:
                land_scores[0] += forest * self.WEIGHTS['forest_fraction']['weight']
                evidence.append(f"forest_fraction_{forest:.2f}")
                sources.append("Copernicus")
            elif pd.isna(forest):
                missing.append("Copernicus_Forest")
            if pd.notna(cropland) and cropland > 0.3:
                land_scores[2] += cropland * self.WEIGHTS['cropland_fraction']['weight']
                evidence.append(f"cropland_fraction_{cropland:.2f}")
                sources.append("Copernicus")
            elif pd.isna(cropland):
                missing.append("Copernicus_Cropland")
            if pd.notna(industrial) and industrial > 0:
                land_scores[1] += min(industrial, 10) * (self.WEIGHTS['industrial_count']['weight'] / 5.0)
                evidence.append(f"industrial_count_{int(industrial)}")
                sources.append("OSM_Overpass")
            elif pd.isna(industrial):
                missing.append("OSM_Overpass_Industrial")
            if pd.notna(dist_industry) and dist_industry < 2000:
                prox_score = (2000 - dist_industry) * 0.001
                land_scores[1] += prox_score
                evidence.append(f"close_to_industry_{int(dist_industry)}m")
                sources.append("OSM_Overpass")

            # ---- Combine land and other scores 50/50 ----
            combined_scores = {cls: 0.5 * land_scores[cls] + 0.5 * other_scores[cls] for cls in land_scores}

            # ---- Softmax to probabilities with smoothing ----
            score_vals = np.array(list(combined_scores.values()))
            if score_vals.sum() == 0:
                probs = np.array([0.25, 0.25, 0.25, 0.25])
            else:
                exp_scores = np.exp(score_vals - np.max(score_vals))
                probs = exp_scores / exp_scores.sum()
            probs = np.clip(probs * 0.98 + 0.01, 0, 0.99)

            max_prob = np.max(probs)
            pred_idx = int(np.argmax(probs))
            if max_prob >= self.EVIDENCE_THRESHOLD:
                final_label = self.CLASS_MAP[pred_idx]
                final_type = 'confident'
            else:
                final_label = self.CLASS_MAP[-1]
                final_type = 'uncertain'

            item_id = row.name if hasattr(row, 'name') and row.name is not None else row.get('id', idx)

            results.append({
                'id': item_id,
                'label': final_label,
                'label_idx': pred_idx if max_prob >= self.EVIDENCE_THRESHOLD else -1,
                'label_type': final_type,
                'label_confidence': float(max_prob),
                'label_evidence': evidence,
                'label_sources': list(set(sources)),
                'missing_sources': list(set(missing)),
                'probs': {c: float(p) for c, p in zip(combined_scores.keys(), probs)}
            })
        df_res = pd.DataFrame(results)
        if 'id' in df_res.columns:
            df_res.set_index('id', inplace=True)
        return df_res
