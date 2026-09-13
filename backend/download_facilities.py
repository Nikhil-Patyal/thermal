import os
import json
import time
import math
import requests
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotspots.models import Hotspot, FacilityCandidate
from django.contrib.gis.geos import Point

HARDCOPY_PATH = os.path.join(os.path.dirname(__file__), 'data', 'india_industrial_facilities.geojson')

def run():
    print("Finding 1x1 degree tiles in India containing hotspots...")
    hotspots = Hotspot.objects.filter(
        latitude__gte=6, latitude__lte=36,
        longitude__gte=68, longitude__lte=98,
        latitude__isnull=False, longitude__isnull=False
    ).values('latitude', 'longitude')
    
    tiles = set()
    for h in hotspots:
        tiles.add((math.floor(h['latitude']), math.floor(h['longitude'])))
        
    print(f"Found {len(tiles)} tiles. Downloading industrial infrastructure from OSM...")
    
    features = []
    
    # We will query overpass
    # Limit to top tiles by density if there are too many to avoid long execution, but we'll try to do them all
    for idx, (lat_t, lon_t) in enumerate(list(tiles)):
        print(f"[{idx+1}/{len(tiles)}] Fetching tile {lat_t}, {lon_t}...")
        bbox = f"{lat_t},{lon_t},{lat_t+1},{lon_t+1}"
        query = f"""
        [out:json][timeout:25];
        (
          node["landuse"="industrial"]({bbox});
          way["landuse"="industrial"]({bbox});
          node["man_made"~"works|chimney"]({bbox});
        );
        out center tags;
        """
        try:
            res = requests.post("https://overpass-api.de/api/interpreter", data={'data': query}, timeout=30)
            if res.status_code == 200:
                data = res.json()
                for el in data.get('elements', []):
                    lat = el.get('lat') or el.get('center', {}).get('lat')
                    lon = el.get('lon') or el.get('center', {}).get('lon')
                    tags = el.get('tags', {})
                    name = tags.get('name', 'Unknown Facility')
                    if lat and lon:
                        features.append({
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [lon, lat]
                            },
                            "properties": {
                                "name": name,
                                "category": "industrial"
                            }
                        })
            elif res.status_code == 429:
                print("Rate limited by Overpass. Sleeping 10s...")
                time.sleep(10)
        except Exception as e:
            print(f"Error fetching tile: {e}")
            
        # Polite sleep
        time.sleep(1)
        
    print(f"Downloaded {len(features)} industrial facilities.")
    
    # Save hardcopy
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    with open(HARDCOPY_PATH, 'w') as f:
        json.dump(geojson, f, indent=2)
    print(f"Saved hardcopy to {HARDCOPY_PATH}")
    
    # Insert into database
    print("Loading into FacilityCandidate table...")
    FacilityCandidate.objects.all().delete() # clear old
    
    objs = []
    for f in features:
        lon, lat = f['geometry']['coordinates']
        name = f['properties']['name']
        objs.append(FacilityCandidate(
            name=name,
            category='industrial',
            geometry=Point(lon, lat, srid=4326)
        ))
        
    FacilityCandidate.objects.bulk_create(objs, batch_size=1000)
    print("Database loaded successfully.")

if __name__ == '__main__':
    run()
