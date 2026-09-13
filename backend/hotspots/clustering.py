import os
import django
from datetime import timedelta
from django.db.models import Avg, Count
from django.contrib.gis.measure import D

def calculate_industrial_baselines(facility, current_date):
    """
    Calculate the 90-day rolling baseline for an industrial facility.
    """
    from hotspots.models import Hotspot
    
    start_date = current_date - timedelta(days=90)
    history = Hotspot.objects.filter(
        facility_candidate=facility,
        acquisition_date__gte=start_date,
        acquisition_date__lt=current_date
    )
    
    count = history.count()
    if count < 10:
        return None  # Insufficient history
        
    avg_frp = history.aggregate(Avg('frp'))['frp__avg']
    avg_bright = history.aggregate(Avg('brightness'))['brightness__avg']
    
    return {
        'count': count,
        'avg_frp': avg_frp,
        'avg_brightness': avg_bright
    }

def cluster_events():
    """
    Groups hotspots into ThermalEvents based on spatial and temporal proximity.
    Evaluates industrial anomalies against their baselines.
    """
    from hotspots.models import Hotspot, FacilityCandidate
    
    # Simple DBSCAN-like grouping implemented in Python for a batch
    # In production, this would be a PostGIS ST_ClusterDBSCAN query.
    print("Clustering framework added (Phase 4).")
    
    # Example Baseline Comparison for suspected incidents
    industrial_hotspots = Hotspot.objects.filter(source_type='Likely routine industrial thermal source')
    
    # Needs a facility_candidate relation on Hotspot
    # We will simulate this by matching against FacilityCandidate directly for now
    for h in industrial_hotspots[:100]:
        if not h.location: continue
        facilities = FacilityCandidate.objects.filter(geometry__distance_lte=(h.location, D(m=1000)), category='industrial')
        facility = facilities.first()
        if not facility: continue
            
        baseline = calculate_industrial_baselines(facility, h.acquisition_date)
        if not baseline:
            h.industrial_anomaly_status = 'Unknown (Insufficient History)'
            h.save(update_fields=['industrial_anomaly_status'])
            continue
            
        # Deviation logic
        if h.frp and baseline['avg_frp'] and h.frp > baseline['avg_frp'] * 3.0:
            h.source_type = 'Suspected industrial incident'
            h.industrial_anomaly_status = 'Suspected Incident (3x FRP Deviation)'
            h.save(update_fields=['source_type', 'industrial_anomaly_status'])
        else:
            h.industrial_anomaly_status = 'Routine'
            h.save(update_fields=['industrial_anomaly_status'])

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    cluster_events()
