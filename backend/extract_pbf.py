import osmium
import csv
import os

class IndustryHandler(osmium.SimpleHandler):
    def __init__(self, writer):
        super(IndustryHandler, self).__init__()
        self.writer = writer
        self.count = 0

    def process_element(self, element, geom_type):
        tags = element.tags
        if 'landuse' in tags and tags['landuse'] == 'industrial':
            category = 'Industrial'
        elif 'industrial' in tags and tags['industrial'] == 'mine':
            category = 'Mine'
        elif 'man_made' in tags and tags['man_made'] in ('mineshaft', 'adit', 'works'):
            category = 'Industrial'
        else:
            return

        name = tags.get('name', 'Unknown Facility')

        try:
            if geom_type == 'node':
                lat = element.location.lat
                lon = element.location.lon
            elif geom_type == 'way':
                # Calculate centroid of the way
                nodes = list(element.nodes)
                if not nodes:
                    return
                lat = sum(n.location.lat for n in nodes) / len(nodes)
                lon = sum(n.location.lon for n in nodes) / len(nodes)
            else:
                return

            self.writer.writerow([name, category, lat, lon])
            self.count += 1
            if self.count % 5000 == 0:
                print(f"Extracted {self.count} facilities...")
        except osmium.InvalidLocationError:
            pass
        except Exception as e:
            pass

    def node(self, n):
        self.process_element(n, 'node')

    def way(self, w):
        self.process_element(w, 'way')

def main():
    pbf_file = 'data/india-latest.osm.pbf'
    out_file = 'data/industrial_and_mines_data.csv'

    print("Starting extraction...")
    with open(out_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Category', 'Latitude', 'Longitude'])

        handler = IndustryHandler(writer)
        # Apply the node cache for ways
        idx = 'flex_mem'
        location_handler = osmium.NodeLocationsForWays(osmium.index.create_map(idx))
        
        # Apply the handlers
        handler.apply_file(pbf_file, locations=True, idx=idx)

    print(f"Done! Extracted {handler.count} facilities.")

if __name__ == '__main__':
    main()
