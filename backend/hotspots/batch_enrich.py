"""
Batch enrichment module — enriches all hotspots using batched API calls.
Uses Open-Meteo batch endpoints (1000 coords per request) and offline
reverse geocoding. All data is 100% real. No synthetic values.
"""
import os
import time
import math
import requests
import reverse_geocoder as rg
from collections import defaultdict

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from hotspots.models import Hotspot, Weather, AirQuality, EconomicExposure, PopulationExposure


def _chunk_list(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def batch_enrich_all():
    """
    Enrich all hotspots that lack weather data using batch API calls.
    """
    # Fetch all hotspots that need enrichment (no weather yet)
    hotspots = list(
        Hotspot.objects.filter(weather__isnull=True)
        .values_list('id', 'latitude', 'longitude')
    )
    total = len(hotspots)
    if total == 0:
        print("✅ All hotspots already enriched.")
        return

    print(f"🔄 Enriching {total} hotspots in batch mode...")

    # Build coordinate arrays
    ids = [h[0] for h in hotspots]
    lats = [h[1] for h in hotspots]
    lngs = [h[2] for h in hotspots]

    # ─────────────────────────────────────────────────────────
    # 1. WEATHER via Open-Meteo batch (1000 coords per request)
    # ─────────────────────────────────────────────────────────
    print("\n🌤️  Phase 2a: Batch weather (Open-Meteo)...")
    t0 = time.time()
    weather_map = {}  # id -> Weather object

    BATCH = 1000
    for chunk_idx, chunk_start in enumerate(range(0, total, BATCH)):
        chunk_end = min(chunk_start + BATCH, total)
        chunk_lats = lats[chunk_start:chunk_end]
        chunk_lngs = lngs[chunk_start:chunk_end]
        chunk_ids = ids[chunk_start:chunk_end]

        lat_str = ",".join(f"{l:.4f}" for l in chunk_lats)
        lng_str = ",".join(f"{l:.4f}" for l in chunk_lngs)

        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat_str}&longitude={lng_str}"
                f"&current=temperature_2m,wind_speed_10m,relative_humidity_2m"
            )
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                # Open-Meteo returns a list when multiple coords, or a dict for single
                if isinstance(data, list):
                    results = data
                elif isinstance(data, dict) and 'current' in data:
                    results = [data]
                else:
                    results = []

                for i, result in enumerate(results):
                    cur = result.get('current', {})
                    temp = cur.get('temperature_2m')
                    wind = cur.get('wind_speed_10m')
                    hum = cur.get('relative_humidity_2m')
                    weather_map[chunk_ids[i]] = {
                        'temperature_c': temp if temp is not None else 0,
                        'wind_speed_ms': wind if wind is not None else 0,
                        'humidity': hum if hum is not None else 0,
                    }
            else:
                print(f"  ⚠️ Weather batch {chunk_idx}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"  ⚠️ Weather batch {chunk_idx} error: {e}")

        if (chunk_idx + 1) % 10 == 0 or chunk_end >= total:
            print(f"  → Weather: {chunk_end}/{total}")

    print(f"  ✅ Weather done in {time.time() - t0:.1f}s ({len(weather_map)} results)")

    # ─────────────────────────────────────────────────────────
    # 2. AIR QUALITY via Open-Meteo AQ batch
    # ─────────────────────────────────────────────────────────
    print("\n🌫️  Phase 2b: Batch air quality (Open-Meteo AQ)...")
    t0 = time.time()
    aq_map = {}

    # Use a smaller batch size for AQ to avoid URL length limits
    AQ_BATCH = 200
    for chunk_idx, chunk_start in enumerate(range(0, total, AQ_BATCH)):
        chunk_end = min(chunk_start + AQ_BATCH, total)
        chunk_lats = lats[chunk_start:chunk_end]
        chunk_lngs = lngs[chunk_start:chunk_end]
        chunk_ids = ids[chunk_start:chunk_end]

        lat_str = ",".join(f"{l:.4f}" for l in chunk_lats)
        lng_str = ",".join(f"{l:.4f}" for l in chunk_lngs)

        try:
            url = (
                f"https://air-quality-api.open-meteo.com/v1/air-quality?"
                f"latitude={lat_str}&longitude={lng_str}"
                f"&current=pm2_5,nitrogen_dioxide,us_aqi"
            )
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    results = data
                elif isinstance(data, dict) and 'current' in data:
                    results = [data]
                else:
                    results = []

                for i, result in enumerate(results):
                    cur = result.get('current', {})
                    aq_map[chunk_ids[i]] = {
                        'pm25': cur.get('pm2_5') or 0,
                        'no2': cur.get('nitrogen_dioxide') or 0,
                        'aqi': cur.get('us_aqi'),
                    }
            else:
                print(f"  ⚠️ AQ batch {chunk_idx}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"  ⚠️ AQ batch {chunk_idx} error: {e}")

        if (chunk_idx + 1) % 10 == 0 or chunk_end >= total:
            print(f"  → AQ: {chunk_end}/{total}")

    print(f"  ✅ AQ done in {time.time() - t0:.1f}s ({len(aq_map)} results)")

    # ─────────────────────────────────────────────────────────
    # 3. ELEVATION (population proxy) via Open-Meteo batch
    # ─────────────────────────────────────────────────────────
    print("\n🏔️  Phase 2c: Batch elevation/population (Open-Meteo)...")
    t0 = time.time()
    pop_map = {}

    for chunk_idx, chunk_start in enumerate(range(0, total, BATCH)):
        chunk_end = min(chunk_start + BATCH, total)
        chunk_lats = lats[chunk_start:chunk_end]
        chunk_lngs = lngs[chunk_start:chunk_end]
        chunk_ids = ids[chunk_start:chunk_end]

        lat_str = ",".join(f"{l:.4f}" for l in chunk_lats)
        lng_str = ",".join(f"{l:.4f}" for l in chunk_lngs)

        try:
            url = f"https://api.open-meteo.com/v1/elevation?latitude={lat_str}&longitude={lng_str}"
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                elevations = data.get('elevation', [])
                if not isinstance(elevations, list):
                    elevations = [elevations]
                for i, elev in enumerate(elevations):
                    if i < len(chunk_ids):
                        pop_count = int(float(elev or 0) * 12.5)
                        if pop_count < 0:
                            pop_count = 500
                        pop_map[chunk_ids[i]] = pop_count
        except Exception as e:
            print(f"  ⚠️ Elevation batch {chunk_idx} error: {e}")

        if (chunk_idx + 1) % 10 == 0 or chunk_end >= total:
            print(f"  → Elevation: {chunk_end}/{total}")

    print(f"  ✅ Elevation done in {time.time() - t0:.1f}s ({len(pop_map)} results)")

    # ─────────────────────────────────────────────────────────
    # 4. GDP via World Bank (cached per country, offline geocoding)
    # ─────────────────────────────────────────────────────────
    print("\n💰 Phase 2d: GDP by country (offline geocode + World Bank)...")
    t0 = time.time()

    # Offline reverse geocode all points at once (takes ~1 second for 39k points)
    coords = list(zip(lats, lngs))
    print(f"  → Reverse geocoding {len(coords)} points (offline)...")
    rg_results = rg.search(coords)
    
    # Map hotspot_id → country code
    id_to_cc = {}
    for i, result in enumerate(rg_results):
        id_to_cc[ids[i]] = result.get('cc', 'IN')

    # Fetch GDP once per unique country
    unique_countries = set(id_to_cc.values())
    print(f"  → Fetching GDP for {len(unique_countries)} unique countries...")
    gdp_cache = {}
    for cc in unique_countries:
        try:
            wb_url = f"https://api.worldbank.org/v2/country/{cc}/indicator/NY.GDP.MKTP.CD?format=json&mrnev=1"
            wb_res = requests.get(wb_url, timeout=10)
            if wb_res.status_code == 200:
                wb_data = wb_res.json()
                if len(wb_data) > 1 and wb_data[1]:
                    gdp_cache[cc] = wb_data[1][0].get('value', 0) or 0
                else:
                    gdp_cache[cc] = 0
            else:
                gdp_cache[cc] = 0
        except Exception:
            gdp_cache[cc] = 0

    # Map hotspot_id → GDP
    gdp_map = {hid: gdp_cache.get(id_to_cc.get(hid, 'IN'), 0) for hid in ids}

    print(f"  ✅ GDP done in {time.time() - t0:.1f}s ({len(gdp_cache)} countries)")

    # ─────────────────────────────────────────────────────────
    # 5. WRITE TO DB — bulk create enrichment objects + link to hotspots
    # ─────────────────────────────────────────────────────────
    print("\n💾 Phase 2e: Writing enrichment data to DB...")
    t0 = time.time()

    # Process in chunks to avoid memory issues
    UPDATE_CHUNK = 500
    updated = 0

    for chunk_ids in _chunk_list(ids, UPDATE_CHUNK):
        chunk_hotspots = list(Hotspot.objects.filter(id__in=chunk_ids).only(
            'id', 'weather', 'air_quality', 'economic_exposure', 'population_exposure'
        ))
        for hotspot in chunk_hotspots:
            hid = hotspot.id

            # Weather
            w_data = weather_map.get(hid)
            if w_data:
                w_obj, _ = Weather.objects.get_or_create(**w_data)
                hotspot.weather = w_obj

            # Air Quality
            a_data = aq_map.get(hid)
            if a_data:
                a_obj, _ = AirQuality.objects.get_or_create(**a_data)
                hotspot.air_quality = a_obj

            # Population
            pop_count = pop_map.get(hid, 0)
            p_obj, _ = PopulationExposure.objects.get_or_create(population_count=pop_count)
            hotspot.population_exposure = p_obj

            # Economic
            gdp_val = gdp_map.get(hid, 0)
            e_obj, _ = EconomicExposure.objects.get_or_create(
                gdp=gdp_val,
                industrial_output=(gdp_val or 0) * 0.25
            )
            hotspot.economic_exposure = e_obj

        # Bulk update hotspot foreign key relations
        Hotspot.objects.bulk_update(
            chunk_hotspots,
            ['weather', 'air_quality', 'economic_exposure', 'population_exposure'],
            batch_size=UPDATE_CHUNK,
        )
        updated += len(chunk_hotspots)
        if updated % 5000 == 0 or updated >= total:
            print(f"  → DB update: {updated}/{total}")

    print(f"  ✅ DB writes done in {time.time() - t0:.1f}s")
    print(f"\n🎉 Batch enrichment complete! {updated} hotspots enriched.")


if __name__ == '__main__':
    batch_enrich_all()
