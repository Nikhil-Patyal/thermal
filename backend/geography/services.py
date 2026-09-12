import requests
import math
import logging
from typing import Dict, Any, List
from django.conf import settings
from .cache import GeographyCache

logger = logging.getLogger(__name__)

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


class GeographyService:
    """
    Utility service that extracts real-world geographic and infrastructure context
    around a latitude/longitude using OpenStreetMap Overpass API and Copernicus APIs.
    """
    OVERPASS_URL = getattr(settings, 'OVERPASS_ENDPOINT', 'https://overpass-api.de/api/interpreter')
    COPERNICUS_API_KEY = getattr(settings, 'COPERNICUS_API_KEY', None)

    @classmethod
    def get_overpass_infrastructure(cls, lat: float, lon: float, radius_m: int) -> Dict[str, Any]:
        """
        Query Overpass API for infrastructure around (lat, lon) within radius in meters.
        Returns counts and distances to industrial sites.
        """
        cached = GeographyCache.get(lat, lon, radius_m, prefix="overpass")
        if cached is not None:
            return cached

        query = f"""
        [out:json][timeout:25];
        (
          node["landuse"="industrial"](around:{radius_m},{lat},{lon});
          way["landuse"="industrial"](around:{radius_m},{lat},{lon});
          node["man_made"="mineshaft"](around:{radius_m},{lat},{lon});
          way["man_made"="mineshaft"](around:{radius_m},{lat},{lon});
          node["man_made"="oil_well"](around:{radius_m},{lat},{lon});
          node["man_made"="pipeline"](around:{radius_m},{lat},{lon});
          way["man_made"="pipeline"](around:{radius_m},{lat},{lon});
          node["power"="plant"](around:{radius_m},{lat},{lon});
          way["power"="plant"](around:{radius_m},{lat},{lon});
          node["power"="generator"](around:{radius_m},{lat},{lon});
        );
        out center tags;
        """
        
        try:
            response = requests.post(cls.OVERPASS_URL, data={'data': query}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                elements = data.get("elements", [])
                
                industrial_count = len(elements)
                min_distance = None
                
                for el in elements:
                    el_lat = el.get("lat") or el.get("center", {}).get("lat")
                    el_lon = el.get("lon") or el.get("center", {}).get("lon")
                    if el_lat is not None and el_lon is not None:
                        d = haversine(lat, lon, el_lat, el_lon)
                        if min_distance is None or d < min_distance:
                            min_distance = d
                
                result = {
                    "source_available": True,
                    "industrial_count": industrial_count,
                    "distance_to_industry": min_distance
                }
                GeographyCache.set(lat, lon, radius_m, result, prefix="overpass")
                return result
            else:
                logger.warning(f"Overpass API error: {response.status_code}")
        except Exception as e:
            logger.error(f"Overpass API exception: {e}")

        # Fallback
        return {
            "source_available": False,
            "industrial_count": None,
            "distance_to_industry": None,
        }

    @classmethod
    def get_copernicus_land_cover(cls, lat: float, lon: float, radius_m: int) -> Dict[str, Any]:
        """
        Query Copernicus API for land cover fractions.
        """
        cached = GeographyCache.get(lat, lon, radius_m, prefix="copernicus")
        if cached is not None:
            return cached

        if not cls.COPERNICUS_API_KEY:
            return {
                "source_available": False,
                "forest_fraction": None,
                "cropland_fraction": None,
                "builtup_fraction": None,
            }

        url = getattr(settings, 'COPERNICUS_ENDPOINT', 'https://api.copernicus.eu/land-cover/v1/fractions')
        params = {
            'lat': lat,
            'lon': lon,
            'radius': radius_m,
            'apikey': cls.COPERNICUS_API_KEY
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                result = {
                    "source_available": True,
                    "forest_fraction": data.get('forest_fraction', 0.0),
                    "cropland_fraction": data.get('cropland_fraction', 0.0),
                    "builtup_fraction": data.get('builtup_fraction', 0.0),
                }
                GeographyCache.set(lat, lon, radius_m, result, prefix="copernicus")
                return result
            else:
                logger.warning(f"Copernicus API error: {response.status_code}")
        except Exception as e:
            logger.error(f"Copernicus API exception: {e}")
            
        return {
            "source_available": False,
            "forest_fraction": None,
            "cropland_fraction": None,
            "builtup_fraction": None,
        }

    @classmethod
    def extract_context_features(cls, lat: float, lng: float) -> Dict[str, Any]:
        """
        Main entry point for feature engineering.
        """
        radii = [50, 100, 250, 500, 1000, 5000]
        features = {}
        
        for radius in radii:
            overpass_data = cls.get_overpass_infrastructure(lat, lng, radius)
            features[f'industrial_count_{radius}m'] = overpass_data.get('industrial_count')
            if radius == 1000:
                features['distance_to_industry'] = overpass_data.get('distance_to_industry')
            features[f'overpass_available_{radius}m'] = overpass_data.get('source_available', False)
            
            copernicus_data = cls.get_copernicus_land_cover(lat, lng, radius)
            features[f'forest_fraction_{radius}m'] = copernicus_data.get('forest_fraction')
            features[f'cropland_fraction_{radius}m'] = copernicus_data.get('cropland_fraction')
            features[f'builtup_fraction_{radius}m'] = copernicus_data.get('builtup_fraction')
            features[f'copernicus_available_{radius}m'] = copernicus_data.get('source_available', False)
            
        return features
