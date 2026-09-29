import os
import urllib.request
import csv
try:
    import osmium
except ImportError:
    print("osmium not found.")
    exit(1)

PBF_FILE = 'data/sri-lanka-latest.osm.pbf'
URL = 'https://download.geofabrik.de/asia/sri-lanka-latest.osm.pbf'
OUT_CSV = 'data/srilanka_industry_data.csv'

def download_file():
    if not os.path.exists(PBF_FILE):
        print(f"Downloading {URL}...")
        urllib.request.urlretrieve(URL, PBF_FILE)
        print("Download complete.")
    else:
        print(f"File {PBF_FILE} already exists.")

class SriLankaIndustrialHandler(osmium.SimpleHandler):
    def __init__(self, writer):
        super(SriLankaIndustrialHandler, self).__init__()
        self.writer = writer
        self.count = 0

    def process_element(self, element, geom_type):
        tags = element.tags
        industrial = tags.get("industrial")
        landuse = tags.get("landuse")
        man_made = tags.get("man_made")
        plant = tags.get("plant")
        power = tags.get("power")
        generator = tags.get("generator:source")
        substance = tags.get("substance")
        
        category = None
        if industrial in ["refinery", "oil", "gas", "petrochemical"] or tags.get("pipeline") == "flare" or substance in ["lng", "oil", "gas"]:
            category = "Oil & Gas / Refinery / LNG"
        elif power == "plant" and generator in ["coal", "gas", "oil"]:
            category = "Thermal Power Plant"
        elif landuse == "quarry" or tags.get("mine") or tags.get("resource") in ["coal", "metal"] or industrial == "mine":
            category = "Mine / quarry"
        elif industrial in ["smelter", "metallurgical", "steel"] or man_made == "works":
            category = "Steel / Metallurgical"
        elif landuse == "industrial" or man_made == "chimney":
            category = "Industrial"
            
        if not category:
            return

        name = tags.get('name', 'Unknown Facility')

        try:
            if geom_type == 'node':
                lat = element.location.lat
                lon = element.location.lon
            elif geom_type == 'way':
                nodes = list(element.nodes)
                if not nodes:
                    return
                lat = sum(n.location.lat for n in nodes) / len(nodes)
                lon = sum(n.location.lon for n in nodes) / len(nodes)
            else:
                return

            self.writer.writerow([name, category, lat, lon])
            self.count += 1
        except Exception:
            pass

    def node(self, n):
        self.process_element(n, 'node')

    def way(self, w):
        self.process_element(w, 'way')

def main():
    download_file()
    print("Parsing Sri Lanka OSM PBF...")
    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Category', 'Latitude', 'Longitude'])
        
        handler = SriLankaIndustrialHandler(writer)
        handler.apply_file(PBF_FILE, locations=True, idx='flex_mem')
        
    print(f"Done! Extracted {handler.count} facilities in Sri Lanka.")
    print(f"Saved to {OUT_CSV}")

if __name__ == '__main__':
    main()
