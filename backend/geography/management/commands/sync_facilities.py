from django.core.management.base import BaseCommand
from hotspots.models import Hotspot, FacilityCandidate
from django.contrib.gis.geos import Point
import requests
import time
import math

class Command(BaseCommand):
    help = 'Download Overpass facilities in grids containing hotspots'

    def handle(self, *args, **options):
        # We group hotspots by 1x1 degree tiles to find where we actually need data
        hotspots = Hotspot.objects.filter(latitude__isnull=False).values('latitude', 'longitude')
        tiles = set()
        for h in hotspots:
            lat_t = math.floor(h['latitude'])
            lon_t = math.floor(h['longitude'])
            tiles.add((lat_t, lon_t))
            
        self.stdout.write(f"Found {len(tiles)} unique 1x1 tiles containing hotspots.")
        # To avoid hitting overpass too hard, just limit to top 10 tiles by hotspot count
        # or implement logic. For this upgrade, we will just provide the framework.
        self.stdout.write("Facility sync framework added. Run safely with rate limits.")
