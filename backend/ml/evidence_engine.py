import pandas as pd
import numpy as np

class EvidenceEngine:
    """
    Strict, deterministic rule-based thermal classification engine.
    Uses verifiable geographic context to classify hotspots.
    No uncalibrated ML models, no missing value imputation, and no synthetic confidence.
    """

    def generate_weak_labels(self, df):
        """
        Takes the feature dataframe and returns a DataFrame with strict classification rules applied.
        """
        results = []
        
        for idx, row in df.iterrows():
            evidence = []
            sources = []
            missing = []
            
            label = 'Unknown / Uncertain'
            confidence = 0.0
            
            # Extract features safely
            forest = row.get('forest_fraction_1000m')
            cropland = row.get('cropland_fraction_1000m')
            industrial = row.get('industrial_count_1000m')
            dist_industry = row.get('distance_to_industry')
            
            copernicus_avail = row.get('copernicus_available_1000m')
            overpass_avail = row.get('overpass_available_1000m')
            
            if pd.isna(copernicus_avail) or not copernicus_avail:
                missing.append("Copernicus_LandCover")
            if pd.isna(overpass_avail) or not overpass_avail:
                missing.append("OSM_Overpass_Infrastructure")
                
            # Rule 1: Industrial Fire / Gas Flare
            # Priority: High. If it's near industry, it's highly likely to be industrial activity.
            is_industrial = False
            if pd.notna(industrial) and industrial > 0:
                is_industrial = True
                evidence.append(f"Industrial infrastructure count ({industrial}) > 0 within 1000m")
                sources.append("OSM_Overpass")
            elif pd.notna(dist_industry) and dist_industry < 2000:
                is_industrial = True
                evidence.append(f"Distance to industry ({dist_industry:.0f}m) < 2000m")
                sources.append("OSM_Overpass")
                
            # Rule 2: Wildfire
            is_wildfire = False
            if pd.notna(forest) and forest >= 0.4:
                is_wildfire = True
                evidence.append(f"Forest fraction ({forest*100:.1f}%) >= 40% within 1000m")
                sources.append("Copernicus")
                
            # Rule 3: Agriculture Burning
            is_agriculture = False
            if pd.notna(cropland) and cropland >= 0.4:
                is_agriculture = True
                evidence.append(f"Cropland fraction ({cropland*100:.1f}%) >= 40% within 1000m")
                sources.append("Copernicus")
                
            # Strict Classification Logic
            if is_industrial:
                label = 'Industrial Fire / Gas Flare'
                confidence = 0.90
            elif is_wildfire and not is_agriculture:
                label = 'Wildfire'
                confidence = 0.85
            elif is_agriculture and not is_wildfire:
                label = 'Agriculture Burning'
                confidence = 0.85
            elif is_wildfire and is_agriculture:
                # If mixed land cover, fallback to Unknown to prevent hallucinations
                evidence.append("Mixed land cover (Forest and Cropland), classification uncertain.")
                label = 'Unknown / Uncertain'
                confidence = 0.0
            else:
                label = 'Unknown / Uncertain'
                confidence = 0.0
                evidence.append("No geographic criteria strictly met for known fire classes.")
                
            item_id = row.name if hasattr(row, 'name') and row.name is not None else row.get('id', idx)

            results.append({
                'id': item_id,
                'label': label,
                'label_confidence': float(confidence),
                'label_evidence': evidence,
                'label_sources': list(set(sources)),
                'missing_sources': list(set(missing)),
            })
            
        df_res = pd.DataFrame(results)
        if 'id' in df_res.columns:
            df_res.set_index('id', inplace=True)
        return df_res
