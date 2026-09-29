import os
import django
import requests
import time
from tqdm import tqdm

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotspots.models import Hotspot, Weather, AirQuality

def fetch_data():
    hotspots = list(Hotspot.objects.filter(
        latitude__gte=6, latitude__lte=38,
        longitude__gte=68, longitude__lte=98,
        latitude__isnull=False, longitude__isnull=False
    ).select_related('weather', 'air_quality'))
    
    total = len(hotspots)
    print(f"Fetching Open-Meteo data for {total} hotspots in batches...")
    
    session = requests.Session()
    batch_size = 50
    
    for i in tqdm(range(0, total, batch_size)):
        batch = hotspots[i:i+batch_size]
        
        # Filter out those that already have weather and air_quality
        batch_to_fetch = [h for h in batch if not h.weather or not h.air_quality]
        
        if not batch_to_fetch:
            continue
            
        lats = ",".join([str(h.latitude) for h in batch_to_fetch])
        lngs = ",".join([str(h.longitude) for h in batch_to_fetch])
        
        try:
            # Weather fetch
            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lngs}&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
            w_res = session.get(w_url, timeout=10)
            
            # AQI fetch
            aq_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lats}&longitude={lngs}&current=pm2_5,nitrogen_dioxide,us_aqi"
            aq_res = session.get(aq_url, timeout=10)
            
            w_data = w_res.json() if w_res.status_code == 200 else []
            aq_data = aq_res.json() if aq_res.status_code == 200 else []
            
            # API returns a dict if 1 location, or a list if multiple locations
            if isinstance(w_data, dict) and 'latitude' in w_data:
                w_data = [w_data]
            elif isinstance(w_data, dict) and 'error' in w_data:
                print("Open-Meteo Error:", w_data)
                w_data = []

            if isinstance(aq_data, dict) and 'latitude' in aq_data:
                aq_data = [aq_data]
            elif isinstance(aq_data, dict) and 'error' in aq_data:
                print("Open-Meteo Air Quality Error:", aq_data)
                aq_data = []
                
            for j, h in enumerate(batch_to_fetch):
                fields_to_save = []
                if not h.weather and j < len(w_data) and w_data[j]:
                    cur = w_data[j].get('current', {})
                    if cur:
                        w_obj = Weather.objects.create(
                            temperature_c=cur.get('temperature_2m'),
                            wind_speed_ms=cur.get('wind_speed_10m'),
                            humidity=cur.get('relative_humidity_2m')
                        )
                        h.weather = w_obj
                        fields_to_save.append('weather')
                        
                if not h.air_quality and j < len(aq_data) and aq_data[j]:
                    aq_cur = aq_data[j].get('current', {})
                    if aq_cur:
                        aq_obj = AirQuality.objects.create(
                            pm25=aq_cur.get('pm2_5'),
                            no2=aq_cur.get('nitrogen_dioxide'),
                            aqi=aq_cur.get('us_aqi')
                        )
                        h.air_quality = aq_obj
                        fields_to_save.append('air_quality')
                        
                if fields_to_save:
                    h.save(update_fields=fields_to_save)
                    
            time.sleep(0.5) # Be nice to the free API (1s per batch is very safe)
        except Exception as e:
            print(f"Error on batch {i}: {e}")

    print("Finished fetching Open-Meteo data!")

if __name__ == '__main__':
    fetch_data()
