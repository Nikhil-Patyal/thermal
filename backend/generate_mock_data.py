import os
import django
import random
from datetime import datetime, timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotspots.models import Hotspot
from django.contrib.gis.geos import Point

def generate_mock_hotspots():
    count = Hotspot.objects.count()
    if count > 0:
        print(f"Already {count} hotspots in the database.")
        return

    print("Generating 100 mock hotspots in India...")
    # Bounding box roughly around central/northern India
    lat_min, lat_max = 17.0, 30.0
    lng_min, lng_max = 70.0, 85.0
    
    classes = ['Wildfire', 'Industrial Fire / Gas Flare', 'Agriculture Burning', 'Mining Activity / Persistent', 'Unknown / Uncertain']

    hotspots = []
    for i in range(100):
        lat = random.uniform(lat_min, lat_max)
        lng = random.uniform(lng_min, lng_max)
        frp = random.uniform(5.0, 300.0)
        confidence = random.randint(30, 100)
        conf_score = random.uniform(0.4, 0.99)
        pred_class = random.choice(classes)
        
        h = Hotspot(
            latitude=lat,
            longitude=lng,
            location=Point(lng, lat, srid=4326),
            frp=frp,
            confidence=confidence,
            confidence_score=conf_score,
            predicted_class=pred_class,
            acquisition_date=datetime.now(timezone.utc),
            brightness=random.uniform(300, 500)
        )
        hotspots.append(h)
    
    Hotspot.objects.bulk_create(hotspots)
    print(f"Successfully created 100 mock hotspots.")

if __name__ == '__main__':
    generate_mock_hotspots()
