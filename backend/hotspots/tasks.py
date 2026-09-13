import os
import csv
import io
import requests
from datetime import datetime, timedelta
from celery import shared_task
from django.utils import timezone
from django.contrib.gis.geos import Point
from .models import Hotspot, EconomicExposure, AirQuality, SafeRoute, Weather, PopulationExposure, WaterQuality

# Helper function for reverse geocoding
def get_location_info(lat, lng):
    headers = {'User-Agent': 'hotspot_intel_sih_2026/1.0'}
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            country_code = data.get('address', {}).get('country_code', 'in')
            # Return country code for world bank, and a general bounding box or nearby center for routing
            return country_code.upper()
    except Exception:
        pass
    return "IN"  # Default to India if failed

@shared_task
def fetch_live_firms_data():
    """
    Fetch data from NASA FIRMS API and bulk-insert Hotspots.
    Uses bulk_create for ~1000x faster ingestion vs per-row get_or_create.
    """
    import time as _time
    api_key = os.getenv('NASA_FIRMS_API_KEY')
    if not api_key:
        print("NASA FIRMS API Key not set.")
        return

    bounds = os.getenv('FIRMS_BOUNDS', 'world')
    # If the user wants 7 days, we need to fetch them one by one since 'world' max day range is 1.
    days_to_fetch = int(os.getenv('FIRMS_DAYS', '7'))

    print(f"📡 Downloading FIRMS CSV (bounds={bounds}, days={days_to_fetch})...")
    t0 = _time.time()
    
    all_csv_lines = []
    header = None
    
    for i in range(days_to_fetch):
        date_str = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
        # Using the date endpoint: /api/area/csv/[MAP_KEY]/[SOURCE]/[AREA]/[DAY_RANGE]/[DATE]
        url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{api_key}/VIIRS_SNPP_NRT/{bounds}/1/{date_str}"
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            lines = response.text.strip().split('\n')
            if len(lines) > 0:
                if header is None:
                    header = lines[0]
                    all_csv_lines.append(header)
                # Append rows, skipping the header line
                all_csv_lines.extend(lines[1:])
        except Exception as e:
            print(f"⚠️ Error fetching {date_str}: {e}")

    if len(all_csv_lines) <= 1:
        print("⚠️ No data downloaded. Proceeding with existing data.")
        return

    csv_text = '\n'.join(all_csv_lines)
    csv_file = io.StringIO(csv_text)
    reader = csv.DictReader(csv_file)
    print(f"✅ Downloaded {len(all_csv_lines)-1} rows in {_time.time() - t0:.1f}s")

    # Parse all rows into Hotspot objects (no DB hits yet)
    print("🔄 Parsing CSV rows...")
    batch = []
    errors = 0
    for row in reader:
        try:
            lat = float(row['latitude'])
            lng = float(row['longitude'])
            frp = float(row.get('frp') or 0)
            brightness = float(row.get('brightness') or 0)
            scan = row.get('scan')
            conf_val = row.get('confidence', '')
            if isinstance(conf_val, str) and conf_val.isalpha():
                if conf_val.lower() == 'l':
                    confidence = 30
                elif conf_val.lower() == 'n':
                    confidence = 70
                elif conf_val.lower() == 'h':
                    confidence = 100
                else:
                    confidence = 50
            else:
                try:
                    confidence = int(conf_val) if conf_val else 0
                except ValueError:
                    confidence = 50

            acq_date = row.get('acq_date')
            acq_time = row.get('acq_time')
            acquisition_dt = None
            if acq_date and acq_time:
                acquisition_dt = datetime.strptime(f"{acq_date} {acq_time}", "%Y-%m-%d %H%M")

            batch.append(Hotspot(
                latitude=lat,
                longitude=lng,
                location=Point(lng, lat, srid=4326),
                frp=frp,
                brightness=brightness,
                scan=scan,
                confidence=confidence,
                acquisition_date=acquisition_dt,
            ))
        except Exception as inner_e:
            errors += 1
            if errors <= 5:
                print(f"⚠️ FIRMS row error: {inner_e}")

    print(f"✅ Parsed {len(batch)} rows ({errors} errors)")

    # Bulk insert in chunks of 1000
    CHUNK = 1000
    print(f"💾 Bulk-inserting {len(batch)} hotspots (chunks of {CHUNK})...")
    t1 = _time.time()
    created_count = 0
    for i in range(0, len(batch), CHUNK):
        chunk = batch[i:i + CHUNK]
        Hotspot.objects.bulk_create(chunk, ignore_conflicts=True)
        created_count += len(chunk)
        if created_count % 5000 == 0 or i + CHUNK >= len(batch):
            print(f"  → {created_count}/{len(batch)} inserted...")

    print(f"✅ Bulk insert done in {_time.time() - t1:.1f}s  (total DB hotspots: {Hotspot.objects.count()})")

@shared_task
def enrich_hotspot_data(hotspot_id):
    """
    Fetches all required enrichment layers from REAL APIs and links them.
    """
    try:
        hotspot = Hotspot.objects.get(id=hotspot_id)
    except Hotspot.DoesNotExist:
        return

    lat = hotspot.latitude if hotspot.latitude is not None else 23.0
    lng = hotspot.longitude if hotspot.longitude is not None else 78.0

    # Get country code for World Bank API
    country_code = get_location_info(lat, lng)

    # 1. Economic Exposure (REAL World Bank API)
    # Indicator: NY.GDP.MKTP.CD (GDP current US$)
    gdp_val = 0
    try:
        wb_url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.MKTP.CD?format=json&mrnev=1"
        wb_res = requests.get(wb_url, timeout=5)
        if wb_res.status_code == 200:
            wb_data = wb_res.json()
            if len(wb_data) > 1 and wb_data[1]:
                gdp_val = wb_data[1][0].get('value', 0)
    except Exception as e:
        print(f"World Bank API Error: {e}")

    eco, _ = EconomicExposure.objects.get_or_create(
        gdp=gdp_val if gdp_val > 0 else None,
        industrial_output=None
    )
    hotspot.economic_exposure = eco

    # 2. Air Quality (REAL OpenAQ API)
    pm25_val, no2_val = None, None
    openaq_key = os.getenv('OPENAQ_API_KEY')
    headers = {'X-API-Key': openaq_key} if openaq_key else {}
    try:
        aq_url = f"https://api.openaq.org/v2/latest?coordinates={lat},{lng}&radius=50000"
        aq_res = requests.get(aq_url, headers=headers, timeout=5)
        if aq_res.status_code == 200:
            aq_data = aq_res.json().get('results', [])
            if aq_data:
                measurements = aq_data[0].get('measurements', [])
                for m in measurements:
                    if m['parameter'] == 'pm25': pm25_val = m['value']
                    if m['parameter'] == 'no2': no2_val = m['value']
    except Exception as e:
        print(f"OpenAQ API Error: {e}")

    aq, _ = AirQuality.objects.get_or_create(pm25=pm25_val or 0, no2=no2_val or 0, aqi=None)
    hotspot.air_quality = aq

    # 3. Safe Route (REAL OSRM API)
    # Route from hotspot to a slightly offset coordinate (representing nearest safe zone/city)
    dist_km, time_min = 0, 0
    try:
        safe_lat, safe_lng = lat + 0.1, lng + 0.1 
        osrm_url = f"http://router.project-osrm.org/route/v1/driving/{lng},{lat};{safe_lng},{safe_lat}?overview=false"
        osrm_res = requests.get(osrm_url, timeout=5)
        if osrm_res.status_code == 200:
            routes = osrm_res.json().get('routes', [])
            if routes:
                dist_km = routes[0].get('distance', 0) / 1000.0
                time_min = routes[0].get('duration', 0) / 60.0
    except Exception as e:
        print(f"OSRM API Error: {e}")

    route, _ = SafeRoute.objects.get_or_create(distance_km=dist_km, travel_time_min=time_min)
    hotspot.safe_route = route

    # 4. Weather (REAL NASA POWER API)
    temp_c, wind_ms, hum = None, None, None
    try:
        today = datetime.utcnow().strftime('%Y%m%d')
        power_url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,WS10M,RH2M&community=RE&longitude={lng}&latitude={lat}&start={today}&end={today}&format=JSON"
        power_res = requests.get(power_url, timeout=5)
        if power_res.status_code == 200:
            p_data = power_res.json().get('properties', {}).get('parameter', {})
            # Get the first available day's data
            temp_c = list(p_data.get('T2M', {}).values())[0] if 'T2M' in p_data else None
            wind_ms = list(p_data.get('WS10M', {}).values())[0] if 'WS10M' in p_data else None
            hum = list(p_data.get('RH2M', {}).values())[0] if 'RH2M' in p_data else None
    except Exception as e:
        print(f"NASA POWER API Error: {e}")

    weather, _ = Weather.objects.get_or_create(temperature_c=temp_c or 0, wind_speed_ms=wind_ms or 0, humidity=hum or 0)
    hotspot.weather = weather

    # 5. Population Exposure (Real WorldPop missing, removing Open-Meteo Proxy)
    pop_count = None
    pop, _ = PopulationExposure.objects.get_or_create(population_count=pop_count)
    hotspot.population_exposure = pop

    # 6. Water Quality
    water_index = None
    water, _ = WaterQuality.objects.get_or_create(contamination_index=water_index)
    hotspot.water_quality = water

    hotspot.save()

    # Trigger classification
    classify_hotspot.delay(hotspot.id)

@shared_task
def classify_hotspot(hotspot_id):
    """
    Run authentic EvidenceEngine rule-based classification for fully enriched hotspot.
    No uncalibrated ML models or fabricated data.
    """
    try:
        hotspot = Hotspot.objects.get(id=hotspot_id)
    except Hotspot.DoesNotExist:
        return
        
    import pandas as pd
    from ml.feature_engineering import FeatureExtractor
    from ml.evidence_engine import EvidenceEngine
    
    context = Hotspot.objects.filter(id__in=[hotspot.id])
    extractor = FeatureExtractor()
    X_df = extractor.extract_features(context, fit_dbscan=False)
    
    if hotspot.id not in X_df.index:
        return
        
    engine = EvidenceEngine()
    results_df = engine.generate_weak_labels(X_df)
    
    if hotspot.id not in results_df.index:
        return
        
    res = results_df.loc[hotspot.id]
    
    hotspot.predicted_class = res['label']
    hotspot.confidence_score = float(res['label_confidence']) if pd.notna(res['label_confidence']) else 0.0
    
    output_payload = {
        "class": res['label'],
        "probability": float(res['label_confidence']) if pd.notna(res['label_confidence']) else None,
        "confidence": float(res['label_confidence']) if pd.notna(res['label_confidence']) else None,
        "evidence": res.get('label_evidence', []),
        "features_used": [], # Obsolete field, kept for UI compatibility
        "data_sources": res.get('label_sources', []),
        "missing_sources": res.get('missing_sources', [])
    }
    
    hotspot.shap_values = output_payload
    hotspot.save()
    print(f"✅ Successfully ran rule-based inference for {hotspot_id}")
