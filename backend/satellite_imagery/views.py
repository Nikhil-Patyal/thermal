import logging
from django.http import JsonResponse, Http404
from django.views import View
from django.shortcuts import get_object_or_404
from hotspots.models import Hotspot
from .models import ImageryCache
from .services import fetch_imagery_for_hotspot

logger = logging.getLogger(__name__)

class HotspotImageryView(View):
    def get(self, request, hotspot_id):
        try:
            hotspot = get_object_or_404(Hotspot, pk=hotspot_id)
            lat = hotspot.location.y
            lng = hotspot.location.x

            # Check db cache
            cache_obj = ImageryCache.objects.filter(hotspot_id=hotspot_id).first()
            if cache_obj and (cache_obj.true_color_url or cache_obj.false_color_url):
                return JsonResponse({
                    "hotspot_id": hotspot_id,
                    "true_color": cache_obj.true_color_url,
                    "false_color": cache_obj.false_color_url,
                    "ndvi": cache_obj.ndvi_url,
                    "nbr": cache_obj.nbr_url,
                    "status": "cached",
                    "error": None
                })
            # Not cached, fetch from service
            data = fetch_imagery_for_hotspot(hotspot_id, lat, lng)

            # Persist to db cache if at least one image returned
            if data.get("true_color") or data.get("false_color"):
                ImageryCache.objects.update_or_create(
                    hotspot_id=hotspot_id,
                    defaults={
                        "true_color_url": data.get("true_color"),
                        "false_color_url": data.get("false_color"),
                        "ndvi_url": data.get("ndvi"),
                        "nbr_url": data.get("nbr"),
                    }
                )

            return JsonResponse({
                "hotspot_id": hotspot_id,
                "true_color": data.get("true_color"),
                "false_color": data.get("false_color"),
                "ndvi": data.get("ndvi"),
                "nbr": data.get("nbr"),
                "status": "success" if (data.get("true_color") or data.get("false_color")) else "empty",
                "error": data.get("error")
            })
        except Http404:
            return JsonResponse({
                "hotspot_id": hotspot_id,
                "error": f"Hotspot with ID {hotspot_id} not found."
            }, status=404)
        except Exception as e:
            logger.exception(f"Error serving satellite imagery for hotspot {hotspot_id}: {e}")
            return JsonResponse({
                "hotspot_id": hotspot_id,
                "error": str(e)
            }, status=500)


class HotspotGroundImageryView(View):
    """
    Isolated API endpoint returning real geotagged ground-level photographs
    near a FIRMS hotspot using Mapillary API.
    Returns available=False if no real photo exists within 500m.
    """
    def get(self, request, hotspot_id):
        try:
            from .ground_services import fetch_ground_imagery_for_hotspot

            hotspot = get_object_or_404(Hotspot, pk=hotspot_id)
            lat = hotspot.location.y
            lng = hotspot.location.x

            result = fetch_ground_imagery_for_hotspot(hotspot_id=hotspot_id, lat=lat, lng=lng)
            result["hotspot_id"] = hotspot_id
            result["hotspot_latitude"] = lat
            result["hotspot_longitude"] = lng
            result["predicted_class"] = hotspot.predicted_class

            return JsonResponse(result)
        except Http404:
            return JsonResponse({
                "hotspot_id": hotspot_id,
                "available": False,
                "reason": f"Hotspot with ID {hotspot_id} not found."
            }, status=404)
        except Exception as e:
            logger.exception(f"Error serving ground imagery for hotspot {hotspot_id}: {e}")
            return JsonResponse({
                "hotspot_id": hotspot_id,
                "available": False,
                "reason": f"Internal error querying ground imagery: {str(e)}"
            }, status=500)
