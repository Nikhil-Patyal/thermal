import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from hotspots.models import Hotspot

class FeatureExtractor:
    """
    Extracts strictly real features from Django ORM Hotspot models 
    into a Pandas DataFrame for ML training and prediction.
    """
    # Import the new geography service
    from geography.services import GeographyService
    
    def extract_features(self, hotspots_queryset, fit_dbscan=False):
        """
        Converts a Django queryset of Hotspots into a DataFrame of numerical features.
        """
        records = []
        for h in hotspots_queryset:
            # 1. Base FIRMS features
            frp = h.frp if h.frp is not None else np.nan
            brightness = h.brightness if h.brightness is not None else np.nan
            
            # Temporal
            is_day = np.nan
            if h.acquisition_date:
                hour = h.acquisition_date.hour
                is_day = 1 if 6 <= hour <= 18 else 0
                
            # 2. Weather
            temp_c = np.nan
            wind_ms = np.nan
            humidity = np.nan
            if hasattr(h, 'weather') and h.weather:
                temp_c = h.weather.temperature_c if h.weather.temperature_c is not None else np.nan
                wind_ms = h.weather.wind_speed_ms if h.weather.wind_speed_ms is not None else np.nan
                humidity = h.weather.humidity if h.weather.humidity is not None else np.nan
                
            # 3. Population & Economy (from our enrichment)
            pop_count = np.nan
            if hasattr(h, 'population_exposure') and h.population_exposure:
                pop_count = h.population_exposure.population_count if h.population_exposure.population_count is not None else np.nan
                
            gdp = np.nan
            if hasattr(h, 'economic_exposure') and h.economic_exposure:
                gdp = h.economic_exposure.gdp if h.economic_exposure.gdp is not None else np.nan
                
            lat = h.latitude if h.latitude is not None else np.nan
            lng = h.longitude if h.longitude is not None else np.nan

            records.append({
                'id': h.id,
                'lat': lat,
                'lng': lng,
                'frp': float(frp) if pd.notna(frp) else np.nan,
                'brightness': float(brightness) if pd.notna(brightness) else np.nan,
                'is_day': float(is_day) if pd.notna(is_day) else np.nan,
                'temp_c': float(temp_c) if pd.notna(temp_c) else np.nan,
                'wind_ms': float(wind_ms) if pd.notna(wind_ms) else np.nan,
                'humidity': float(humidity) if pd.notna(humidity) else np.nan,
                'pop_count': float(pop_count) if pd.notna(pop_count) else np.nan,
                'gdp': float(gdp) if pd.notna(gdp) else np.nan,
            })
            
        df = pd.DataFrame(records)
        
        # -----------------------------------------------------------------
        # 5. Enrich with geographic context (land‑cover fractions, infrastructure)
        # -----------------------------------------------------------------
        # For each hotspot we query the GeographyService. This is a relatively
        # expensive per‑row operation, but the dataset size used for training
        # (≈10 k) is still manageable. In production we would vectorise this or
        # cache results aggressively.
        from tqdm import tqdm
        geo_features = []
        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Geography enrichment"):
            lat, lng = row['lat'], row['lng']
            if pd.isna(lat) or pd.isna(lng):
                # No location -> all geo features are missing
                geo_features.append({})
                continue
            try:
                geo = GeographyService.extract_context_features(lat, lng)
            except Exception as e:
                # On any failure we fall back to empty dict; the service itself
                # records source availability flags.
                geo = {}
            geo_features.append(geo)
        # Convert list of dicts to DataFrame and merge (left‑join on index)
        geo_df = pd.DataFrame(geo_features, index=df.index)
        df = pd.concat([df, geo_df], axis=1)
        
        if df.empty:
            return df
            
        # 4. Spatial Clustering (DBSCAN density feature)
        df['cluster_id'] = -1
        df['cluster_density'] = np.nan
        df['centroid_dist'] = np.nan # Distance from cluster centroid
        
        valid_coords_mask = df['lat'].notna() & df['lng'].notna()
        if valid_coords_mask.any():
            coords = df.loc[valid_coords_mask, ['lat', 'lng']].values
            # epsilon roughly 5km
            db = DBSCAN(eps=0.05, min_samples=3).fit(coords)
            df.loc[valid_coords_mask, 'cluster_id'] = db.labels_
            
            cluster_sizes = df.loc[valid_coords_mask].groupby('cluster_id').size()
            df.loc[valid_coords_mask, 'cluster_density'] = df.loc[valid_coords_mask, 'cluster_id'].map(
                lambda x: cluster_sizes.get(x, 1) if x != -1 else 1
            )
            
            # Simple centroid distance approximation
            for c_id in set(db.labels_):
                if c_id == -1: continue
                mask = (df['cluster_id'] == c_id) & valid_coords_mask
                c_lat, c_lng = df.loc[mask, 'lat'].mean(), df.loc[mask, 'lng'].mean()
                df.loc[mask, 'centroid_dist'] = np.sqrt((df.loc[mask, 'lat'] - c_lat)**2 + (df.loc[mask, 'lng'] - c_lng)**2)

        df.set_index('id', inplace=True)
        return df


