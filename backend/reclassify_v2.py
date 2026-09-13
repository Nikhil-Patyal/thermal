import os
import django
import pandas as pd
from tqdm import tqdm
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotspots.models import Hotspot, ModelVersion
from ml.evidence_engine import EvidenceEngine
from django.contrib.gis.geos import Point

def run():
    print("Initializing Reclassification (v2)...")
    
    # Versioning
    version, _ = ModelVersion.objects.get_or_create(
        version_string="v2.0.0-SIH-Strict",
        defaults={'description': "Strict true-polygon evidence engine without fabricated percentages."}
    )
    
    print("Fetching Indian hotspots...")
    hotspots = Hotspot.objects.filter(
        latitude__gte=6, latitude__lte=38,
        longitude__gte=68, longitude__lte=98,
        latitude__isnull=False, longitude__isnull=False
    )
    
    total = hotspots.count()
    print(f"Total Hotspots to reclassify: {total}")
    
    engine = EvidenceEngine()
    
    batch_size = 500
    updates = []
    
    # Process in batches to avoid overwhelming memory
    # Load all into a dataframe for batch classification
    
    df_data = []
    hotspot_objs = {}
    
    for h in tqdm(hotspots, desc="Loading data"):
        hotspot_objs[h.id] = h
        df_data.append({
            'id': h.id,
            'latitude': h.latitude,
            'longitude': h.longitude,
            'scan': h.scan,
            'track': h.track,
            'frp': h.frp,
            'brightness': h.brightness,
            'forest_fraction_1000m': h.features.get('forest_fraction_1000m') if h.features else None,
            'cropland_fraction_1000m': h.features.get('cropland_fraction_1000m') if h.features else None,
            'industrial_count_1000m': h.features.get('industrial_count_1000m') if h.features else None,
            'distance_to_industry': h.features.get('distance_to_industry') if h.features else None,
            'copernicus_available_1000m': h.features.get('copernicus_available_1000m') if h.features else None,
            'overpass_available_1000m': h.features.get('overpass_available_1000m') if h.features else None,
        })
        
    df = pd.DataFrame(df_data)
    if 'id' in df.columns:
        df.set_index('id', inplace=True)
    
    print("Running EvidenceEngine generate_weak_labels...")
    # This might take a while because it does individual PostGIS queries.
    df_res = engine.generate_weak_labels(df)
    
    print("Applying labels and checking temporal context...")
    for idx, row in tqdm(df_res.iterrows(), total=len(df_res)):
        h = hotspot_objs[idx]
        
        # 1. Update Core classification
        h.predicted_class = row['label']
        h.confidence_score = row['label_confidence_str']
        h.label = row['label']
        h.label_confidence = row['label_confidence_str']
        h.label_evidence = row['label_evidence']
        h.label_sources = row['label_sources']
        h.missing_sources = row['missing_sources']
        h.model_version = version
        h.source_type = row['label']
        
        # 2. Temporal Anomaly Context (Check last 30 days)
        # Only do this if it's an industrial anomaly
        if "Industrial" in h.predicted_class or "Mining" in h.predicted_class:
            if h.acquisition_date and h.location:
                thirty_days_ago = h.acquisition_date - timedelta(days=30)
                # Count previous detections within 500m
                past_detections = Hotspot.objects.filter(
                    acquisition_date__gte=thirty_days_ago,
                    acquisition_date__lt=h.acquisition_date,
                    location__distance_lte=(h.location, 500/111000.0) # ~500m
                ).count()
                
                if past_detections > 3:
                    h.industrial_anomaly_status = "Routine-pattern evidence"
                elif past_detections == 0:
                    h.industrial_anomaly_status = "Unusual-pattern evidence"
                else:
                    h.industrial_anomaly_status = "Insufficient baseline"
            else:
                h.industrial_anomaly_status = "Insufficient baseline"
        else:
            h.industrial_anomaly_status = None
            
        updates.append(h)
        
        if len(updates) >= batch_size:
            Hotspot.objects.bulk_update(updates, [
                'predicted_class', 'confidence_score', 'label', 'label_confidence',
                'label_evidence', 'label_sources', 'missing_sources', 'model_version',
                'source_type', 'industrial_anomaly_status'
            ])
            updates = []
            
    if updates:
        Hotspot.objects.bulk_update(updates, [
            'predicted_class', 'confidence_score', 'label', 'label_confidence',
            'label_evidence', 'label_sources', 'missing_sources', 'model_version',
            'source_type', 'industrial_anomaly_status'
        ])
        
    print(f"Successfully reclassified {total} hotspots.")

if __name__ == '__main__':
    run()
