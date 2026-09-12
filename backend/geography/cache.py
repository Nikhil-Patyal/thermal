import os
import json
import hashlib
from django.conf import settings

# Default cache directory if not set in settings
CACHE_DIR = getattr(settings, 'GEOGRAPHY_CACHE_DIR', os.path.join(settings.BASE_DIR, '.cache', 'geography'))

class GeographyCache:
    """
    A simple file-based cache to avoid hammering external APIs (Overpass, Copernicus)
    during development and bulk extraction.
    """
    @staticmethod
    def _get_key(lat, lon, radius, prefix):
        # Round coordinates to 4 decimal places (~11m at equator) to increase cache hit rate
        # and avoid floating point inaccuracies
        lat_r = round(float(lat), 4)
        lon_r = round(float(lon), 4)
        raw = f"{prefix}_{lat_r}_{lon_r}_{radius}"
        return hashlib.md5(raw.encode('utf-8')).hexdigest()

    @staticmethod
    def _get_filepath(key):
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR, exist_ok=True)
        return os.path.join(CACHE_DIR, f"{key}.json")

    @classmethod
    def get(cls, lat, lon, radius, prefix):
        key = cls._get_key(lat, lon, radius, prefix)
        filepath = cls._get_filepath(key)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    @classmethod
    def set(cls, lat, lon, radius, data, prefix):
        key = cls._get_key(lat, lon, radius, prefix)
        filepath = cls._get_filepath(key)
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass
