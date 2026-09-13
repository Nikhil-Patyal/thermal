import os
import requests
import django
import osmium
from tqdm import tqdm

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotspots.models import FacilityCandidate
from django.contrib.gis.geos import GEOSGeometry

URL = "http://download.geofabrik.de/asia/india-latest.osm.pbf"
PBF_FILE = os.path.join(os.path.dirname(__file__), 'data', 'india-latest.osm.pbf')

def download_file():
    if os.path.exists(PBF_FILE):
        print(f"File {PBF_FILE} already exists.")
        return
    print(f"Downloading {URL}...")
    os.makedirs(os.path.dirname(PBF_FILE), exist_ok=True)
    response = requests.get(URL, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 * 1024
    with open(PBF_FILE, 'wb') as f:
        for data in tqdm(response.iter_content(block_size), total=total_size//block_size, unit='MB'):
            f.write(data)

def map_category(tags):
    landuse = tags.get("landuse")
    man_made = tags.get("man_made")
    industrial = tags.get("industrial")
    if industrial in ["refinery", "oil", "gas"] or tags.get("pipeline") == "flare":
        return "Refinery / oil and gas / flare"
    if landuse == "quarry" or tags.get("mine") or tags.get("resource") in ["coal", "metal"]:
        return "Mine / quarry"
    if industrial in ["smelter", "metallurgical"] or man_made == "works":
        return "Smelter / metallurgical facility"
    if landuse == "industrial" or man_made == "chimney":
        return "Other heat-emitting industrial facility"
    return None

class IndustrialHandler(osmium.SimpleHandler):
    def __init__(self):
        super(IndustrialHandler, self).__init__()
        self.facilities = []
        self.wkbfab = osmium.geom.WKBFactory()

    def add_facility(self, tags, geom_wkb):
        cat = map_category(tags)
        if cat:
            name = tags.get("name", "Unknown Facility")
            self.facilities.append({
                'name': name,
                'category': cat,
                'geom': geom_wkb
            })

    def node(self, n):
        if map_category(n.tags):
            try:
                wkb = self.wkbfab.create_point(n)
                self.add_facility(n.tags, wkb)
            except Exception:
                pass

    def area(self, a):
        if map_category(a.tags):
            try:
                wkb = self.wkbfab.create_multipolygon(a)
                self.add_facility(a.tags, wkb)
            except Exception:
                pass

def process_osm():
    print("Parsing OSM PBF file for areas and nodes... (requires high RAM)")
    handler = IndustrialHandler()
    
    # We use area handler for polygons
    handler.apply_file(PBF_FILE, locations=True, idx='flex_mem')
    
    print(f"Found {len(handler.facilities)} facility footprints.")
    print("Inserting into database...")
    FacilityCandidate.objects.all().delete()
    
    batch = []
    for fac in handler.facilities:
        try:
            geom = GEOSGeometry(fac['geom'])
            batch.append(FacilityCandidate(
                name=fac['name'],
                category=fac['category'],
                geometry=geom
            ))
            if len(batch) >= 1000:
                FacilityCandidate.objects.bulk_create(batch)
                batch = []
        except Exception:
            pass
            
    if batch:
        FacilityCandidate.objects.bulk_create(batch)
        
    print("Facility audit and load complete.")

if __name__ == '__main__':
    download_file()
    process_osm()
