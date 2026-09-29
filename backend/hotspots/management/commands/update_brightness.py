import os
import csv
import io
import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from hotspots.models import Hotspot
import time

class Command(BaseCommand):
    help = 'Fetches FIRMS NRT data for the last 7 days and updates missing brightness values in the database.'

    def handle(self, *args, **options):
        api_key = os.getenv('NASA_FIRMS_API_KEY')
        if not api_key:
            self.stdout.write(self.style.ERROR("NASA FIRMS API Key not set."))
            return

        bounds = 'world'
        days_to_fetch = 7
        
        self.stdout.write(f"📡 Downloading FIRMS CSV (bounds={bounds}, days={days_to_fetch})...")
        t0 = time.time()
        
        # Load all existing hotspots into memory indexed by (rounded_lat, rounded_lng) for fast lookup
        self.stdout.write("Loading existing hotspots for fast matching...")
        # Since we have 360k, we only fetch the ones without bright_ti4
        qs = Hotspot.objects.filter(bright_ti4__isnull=True)
        hotspot_dict = {}
        for h in qs.only('id', 'latitude', 'longitude'):
            if h.latitude and h.longitude:
                # Round to 3 decimals for robust float matching (~110m precision)
                key = (round(h.latitude, 3), round(h.longitude, 3))
                if key not in hotspot_dict:
                    hotspot_dict[key] = []
                hotspot_dict[key].append(h)
                
        self.stdout.write(f"Loaded {len(hotspot_dict)} unique locations to update.")

        updated_count = 0
        batch = []
        
        for i in range(days_to_fetch):
            date_str = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
            url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{api_key}/VIIRS_SNPP_NRT/{bounds}/1/{date_str}"
            try:
                self.stdout.write(f"Fetching {date_str}...")
                response = requests.get(url, stream=True, timeout=120)
                response.raise_for_status()
                
                # Stream decode
                reader = csv.DictReader(line.decode('utf-8') for line in response.iter_lines() if line)
                for row in reader:
                    lat = float(row['latitude'])
                    lng = float(row['longitude'])
                    
                    bright_ti4 = row.get('bright_ti4')
                    if not bright_ti4:
                        continue
                    bright_ti4 = float(bright_ti4)
                    
                    key = (round(lat, 3), round(lng, 3))
                    if key in hotspot_dict:
                        for h in hotspot_dict[key]:
                            h.bright_ti4 = bright_ti4
                            h.brightness = bright_ti4
                            batch.append(h)
                        # Remove to prevent duplicate updates if multiple points match
                        del hotspot_dict[key]
                        
                        if len(batch) >= 1000:
                            Hotspot.objects.bulk_update(batch, ['bright_ti4', 'brightness'])
                            updated_count += len(batch)
                            batch = []
                            self.stdout.write(f"  → Updated {updated_count} hotspots so far...")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️ Error fetching {date_str}: {e}"))

        if batch:
            Hotspot.objects.bulk_update(batch, ['bright_ti4', 'brightness'])
            updated_count += len(batch)

        self.stdout.write(self.style.SUCCESS(f"✅ Successfully updated {updated_count} hotspots with brightness in {time.time() - t0:.1f}s"))
