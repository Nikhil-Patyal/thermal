"""
Mapillary Ground-Level Imagery Service.
Finds real, geotagged crowd-sourced ground-level photographs near FIRMS thermal hotspots.
Strict rules:
- Authentic only. If no image found, returns available=False.
- Progressive search radius: 50m -> 100m -> 250m -> 500m (max).
- Calculates deterministic distance using haversine formula.
- Never fabricates or synthesizes images.
"""
import math
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two coordinates deterministically."""
    r = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 1)


def bounding_box_for_radius(lat: float, lon: float, radius_meters: float) -> str:
    """Compute min_lon,min_lat,max_lon,max_lat string for Mapillary v4 bbox."""
    delta_lat = radius_meters / 111320.0
    cos_lat = math.cos(math.radians(lat))
    delta_lon = radius_meters / (111320.0 * max(abs(cos_lat), 0.0001))
    min_lon = lon - delta_lon
    min_lat = lat - delta_lat
    max_lon = lon + delta_lon
    max_lat = lat + delta_lat
    return f"{min_lon:.6f},{min_lat:.6f},{max_lon:.6f},{max_lat:.6f}"


def fetch_ground_imagery_for_hotspot(hotspot_id: int, lat: float, lng: float) -> dict:
    """
    Search Mapillary API progressively (50m, 100m, 250m, 500m) for real geotagged ground imagery.
    Returns:
      {
        "available": bool,
        "source": "Mapillary",
        "image_id": str or None,
        "image_url": str or None,
        "thumb_2048_url": str or None,
        "distance_from_hotspot_m": float or None,
        "image_latitude": float or None,
        "image_longitude": float or None,
        "captured_at": str or None,
        "reason": str or None
      }
    """
    access_token = getattr(settings, 'MAPILLARY_ACCESS_TOKEN', '').strip()
    if not access_token:
        return {
            "available": False,
            "source": "Mapillary",
            "image_id": None,
            "image_url": None,
            "distance_from_hotspot_m": None,
            "image_latitude": None,
            "image_longitude": None,
            "captured_at": None,
            "reason": "Mapillary access token not configured. Set MAPILLARY_ACCESS_TOKEN in backend/.env to enable real ground imagery search."
        }

    max_radius = getattr(settings, 'GROUND_IMAGERY_MAX_RADIUS_METERS', 500)
    radii = [r for r in [50, 100, 250, 500] if r <= max_radius]
    if not radii:
        radii = [max_radius]

    endpoint = "https://graph.mapillary.com/images"

    for r in radii:
        bbox_str = bounding_box_for_radius(lat, lng, r)
        params = {
            "access_token": access_token,
            "fields": "id,geometry,thumb_1024_url,thumb_2048_url,captured_at",
            "bbox": bbox_str,
            "limit": 10
        }

        try:
            resp = requests.get(endpoint, params=params, timeout=8)
            if resp.status_code != 200:
                err_data = resp.json().get('error', {}) if resp.headers.get('content-type', '').startswith('application/json') else {}
                err_msg = err_data.get('message', f"Mapillary HTTP {resp.status_code}")
                logger.warning(f"Mapillary API error for hotspot {hotspot_id} at {r}m: {err_msg}")
                return {
                    "available": False,
                    "source": "Mapillary",
                    "reason": f"Mapillary service response: {err_msg}"
                }

            data = resp.json().get("data", [])
            if not data:
                continue

            # Find best candidate: closest distance with valid coordinates & image
            candidates = []
            for item in data:
                geom = item.get("geometry", {})
                coords = geom.get("coordinates")
                if not coords or len(coords) < 2:
                    continue
                img_lon, img_lat = coords[0], coords[1]
                dist = haversine_distance_meters(lat, lng, img_lat, img_lon)
                if dist <= r:
                    candidates.append({
                        "item": item,
                        "dist": dist,
                        "lat": img_lat,
                        "lon": img_lon
                    })

            if candidates:
                # Sort by distance first, then most recent capture
                candidates.sort(key=lambda c: (c["dist"], -(c["item"].get("captured_at") or 0)))
                best = candidates[0]
                item = best["item"]

                # Extract captured_at as ISO string if available
                cap_ts = item.get("captured_at")
                captured_at_iso = None
                if cap_ts:
                    try:
                        from datetime import datetime, timezone
                        # Mapillary timestamp is in milliseconds
                        captured_at_iso = datetime.fromtimestamp(cap_ts / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    except Exception:
                        pass

                image_url = item.get("thumb_1024_url") or item.get("thumb_2048_url")
                if image_url:
                    return {
                        "available": True,
                        "source": "Mapillary",
                        "image_id": str(item.get("id")),
                        "image_url": image_url,
                        "thumb_2048_url": item.get("thumb_2048_url"),
                        "distance_from_hotspot_m": best["dist"],
                        "image_latitude": best["lat"],
                        "image_longitude": best["lon"],
                        "captured_at": captured_at_iso,
                        "search_radius_m": r,
                        "reason": None
                    }

        except requests.RequestException as e:
            logger.error(f"Network error querying Mapillary API for hotspot {hotspot_id}: {e}")
            return {
                "available": False,
                "source": "Mapillary",
                "reason": f"Connection error: {str(e)}"
            }

    return {
        "available": False,
        "source": "Mapillary",
        "image_id": None,
        "image_url": None,
        "distance_from_hotspot_m": None,
        "image_latitude": None,
        "image_longitude": None,
        "captured_at": None,
        "reason": f"No real ground-level imagery found within {max_radius} meters of this hotspot."
    }
