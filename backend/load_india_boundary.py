import os
import json
import urllib.request
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotspots.models import IndiaBoundary
from django.contrib.gis.geos import GEOSGeometry

URL = "https://raw.githubusercontent.com/datameet/maps/master/Country/india-composite.geojson"

def load():
    print("Downloading India boundary GeoJSON...")
    try:
        req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        print(f"Datameet failed: {e}. Trying alternative...")
        # Fallback to a simpler OSM boundary for India
        # Nominatim lookup for India (relation 304716)
        NOMINATIM = "https://nominatim.openstreetmap.org/search.php?q=India&polygon_geojson=1&format=jsonv2"
        req = urllib.request.Request(NOMINATIM, headers={'User-Agent': 'Mozilla/5.0 (AGNI-DRISHTI)'})
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            data = None
            for item in res:
                if item.get('osm_type') == 'relation' and item.get('osm_id') == 304716:
                    data = {"features": [{"geometry": item['geojson']}]}
                    break
            if not data:
                print("Failed to find India relation from Nominatim.")
                return

    print("Parsing Geometry...")
    # Get the geometry from the first feature
    if 'features' in data:
        geom_json = data['features'][0]['geometry']
    else:
        geom_json = data['geometry']
        
    geom_str = json.dumps(geom_json)
    
    print("Creating GEOSGeometry...")
    geom = GEOSGeometry(geom_str)
    
    if geom.geom_type == 'Polygon':
        from django.contrib.gis.geos import MultiPolygon
        geom = MultiPolygon(geom)
        
    print("Saving to database...")
    IndiaBoundary.objects.all().delete()
    IndiaBoundary.objects.create(
        name="India",
        geometry=geom,
        source="Nominatim / Datameet"
    )
    print("India boundary successfully loaded!")

if __name__ == '__main__':
    load()
