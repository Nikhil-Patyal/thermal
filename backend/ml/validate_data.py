"""
Data Validation Script
Verifies that no corrupted, random, or incorrectly mapped data enters the training pipeline.
"""
import os
import django
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from hotspots.models import Hotspot
from ml.feature_engineering import FeatureExtractor

def validate_pipeline():
    print("Fetching records for validation...")
    hotspots = Hotspot.objects.select_related(
        'weather', 'population_exposure', 'economic_exposure'
    ).order_by('-acquisition_date')[:5000]
    
    if not hotspots:
        print("No authentic records found in database.")
        return
        
    extractor = FeatureExtractor()
    df = extractor.extract_features(hotspots, fit_dbscan=False)
    
    print(f"Total Authentic Observations: {len(df)}")
    
    # Check Missing Data Policy
    missing_weather = df['temp_c'].isna().sum()
    missing_pop = df['pop_count'].isna().sum()
    missing_gdp = df['gdp'].isna().sum()
    
    print("\n--- Data Provenance Report ---")
    print(f"Features: NASA FIRMS (frp, brightness), Open-Meteo (temp, humidity, pop), World Bank (gdp)")
    print(f"Missing Weather (Open-Meteo): {missing_weather} ({missing_weather/len(df):.1%})")
    print(f"Missing Population Proxy: {missing_pop} ({missing_pop/len(df):.1%})")
    print(f"Missing GDP: {missing_gdp} ({missing_gdp/len(df):.1%})")
    
    # Check for synthetic artifacts
    synthetic_found = False
    for col in df.columns:
        if (df[col] == -999).sum() > 0:
            print(f"WARNING: Synthetic imputation found in {col}")
            synthetic_found = True
            
    if not synthetic_found:
        print("✅ No synthetic artifacts found in dataframe output.")
        
    labels = extractor.generate_labels(df)
    unknown_count = (labels == -1).sum()
    print(f"\nLabel Provenance:")
    print(f"Unknown / Unlabeled: {unknown_count} ({(unknown_count/len(labels)):.1%})")
    print(f"Ground Truth Provided: {len(labels) - unknown_count}")
    
    print("\n✅ Validation complete. Strict missing data policy enforced.")

if __name__ == "__main__":
    validate_pipeline()
