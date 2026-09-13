from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import connection
from .models import Hotspot
from .serializers import HotspotSerializer


class HotspotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for hotspot data.
    - GET /api/hotspots/          -> top 500 full records (for detail cards)
    - GET /api/hotspots/map-points/ -> ALL records, minimal fields only (for map markers)
    - GET /api/hotspots/{id}/     -> single full record
    """
    queryset = Hotspot.objects.all()   # Required by DRF router
    serializer_class = HotspotSerializer

    def list(self, request, *args, **kwargs):
        """Full serializer, limited to 500 records for non-map uses."""
        try:
            limit = int(request.query_params.get('limit', 500))
        except (ValueError, TypeError):
            limit = 500
        limit = min(limit, 2000)
        qs = Hotspot.objects.all().order_by('-frp', '-fetched_at')[:limit]
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve single hotspot details; enrich all fields on-demand using free APIs."""
        instance = self.get_object()

        if instance.location:
            try:
                import requests as ext_requests
                import math
                from .models import Weather, AirQuality, PopulationExposure, SafeRoute, EconomicExposure
                lat = instance.location.y
                lng = instance.location.x
                fields_to_save = []

                # 1. Real Weather via Open-Meteo (Free, no key)
                if not instance.weather:
                    try:
                        w_res = ext_requests.get(
                            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}"
                            f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m",
                            timeout=4
                        )
                        if w_res.status_code == 200:
                            cur = w_res.json().get('current', {})
                            w_obj = Weather.objects.create(
                                temperature_c=cur.get('temperature_2m'),
                                wind_speed_ms=cur.get('wind_speed_10m'),
                                humidity=cur.get('relative_humidity_2m')
                            )
                            instance.weather = w_obj
                            fields_to_save.append('weather')
                    except Exception:
                        pass

                # 2. Real Air Quality via Open-Meteo AQ API (Free, no key)
                if not instance.air_quality:
                    try:
                        aq_res = ext_requests.get(
                            f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lng}"
                            f"&current=pm2_5,nitrogen_dioxide,us_aqi",
                            timeout=4
                        )
                        if aq_res.status_code == 200:
                            aq_cur = aq_res.json().get('current', {})
                            aq_obj = AirQuality.objects.create(
                                pm25=aq_cur.get('pm2_5'),
                                no2=aq_cur.get('nitrogen_dioxide'),
                                aqi=aq_cur.get('us_aqi')
                            )
                            instance.air_quality = aq_obj
                            fields_to_save.append('air_quality')
                    except Exception:
                        pass

                # 3. Population Exposure - estimate based on FRP intensity and area impact
                if not instance.population_exposure:
                    try:
                        frp_val = float(instance.frp or 0)
                        # FRP → impact radius → affected area → population estimate
                        # Based on: radius = sqrt(FRP/10), minimum 5km, max 100km
                        radius_km = min(max(math.sqrt(max(frp_val, 1) / 10.0), 5), 100)
                        area_km2 = math.pi * radius_km ** 2
                        # Density by class type
                        cls = (instance.predicted_class or '').lower()
                        if 'industrial' in cls or 'refinery' in cls or 'mining' in cls:
                            density = 150   # industrial zones are less dense
                        elif 'wildfire' in cls or 'forest' in cls:
                            density = 50    # forest areas are sparse
                        elif 'crop' in cls or 'agricultural' in cls:
                            density = 100   # rural agricultural
                        else:
                            density = 200   # default moderate
                        pop_count = max(int(area_km2 * density), 100)
                        pe_obj = PopulationExposure.objects.create(population_count=pop_count)
                        instance.population_exposure = pe_obj
                        fields_to_save.append('population_exposure')
                    except Exception:
                        pass

                # 4. Safe Route - compute estimated safe evacuation distance from hotspot intensity
                if not instance.safe_route:
                    try:
                        frp = float(instance.frp or 0)
                        # Safe distance based on FRP intensity (MW): higher FRP → larger exclusion zone
                        if frp > 2000:
                            safe_dist_km = round(50 + (frp - 2000) / 500, 1)
                            travel_time = round(safe_dist_km / 60 * 60, 0)  # 60 km/h road speed
                        elif frp > 500:
                            safe_dist_km = round(20 + (frp - 500) / 150, 1)
                            travel_time = round(safe_dist_km / 60 * 60, 0)
                        elif frp > 50:
                            safe_dist_km = round(5 + frp / 50, 1)
                            travel_time = round(safe_dist_km / 50 * 60, 0)
                        else:
                            safe_dist_km = round(2 + frp / 50, 1)
                            travel_time = round(safe_dist_km / 40 * 60, 0)
                        sr_obj = SafeRoute.objects.create(
                            distance_km=safe_dist_km,
                            travel_time_min=travel_time
                        )
                        instance.safe_route = sr_obj
                        fields_to_save.append('safe_route')
                    except Exception:
                        pass

                # 5. Economic Exposure - estimate from World Bank country GDP or FRP-based fallback
                if not instance.economic_exposure:
                    try:
                        frp_val = float(instance.frp or 1)
                        gdp_value = None
                        industrial = None
                        # Try World Bank API via reverse geocode (nominatim – no key)
                        try:
                            nom_res = ext_requests.get(
                                f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json",
                                headers={'User-Agent': 'agni-drishti-thermal-sentinel/1.0'},
                                timeout=4
                            )
                            if nom_res.status_code == 200:
                                addr = nom_res.json().get('address', {})
                                country_code = addr.get('country_code', '').upper()
                                if country_code:
                                    wb_res = ext_requests.get(
                                        f"https://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.MKTP.CD?format=json&mrv=1",
                                        timeout=5
                                    )
                                    if wb_res.status_code == 200:
                                        wb_data = wb_res.json()
                                        if len(wb_data) > 1 and wb_data[1]:
                                            val = wb_data[1][0].get('value')
                                            if val:
                                                gdp_value = float(val)
                                                # Proportion: hotspot area vs country area (rough)
                                                hotspot_area_km2 = math.pi * (min(max(math.sqrt(frp_val / 10.0), 5), 100)) ** 2
                                                country_area_km2 = max(float(nom_res.json().get('boundingbox', [0,0,0,0]) and 1000000), 100000)
                                                industrial = gdp_value * 0.25 * (hotspot_area_km2 / country_area_km2)
                        except Exception:
                            pass
                        # Always fallback to FRP-based estimate if GDP not resolved
                        if gdp_value is None:
                            gdp_value = max(frp_val, 1) * 500000  # $500K GDP exposure per MW FRP
                            industrial = gdp_value * 0.3
                        ee_obj = EconomicExposure.objects.create(
                            gdp=gdp_value,
                            industrial_output=industrial
                        )
                        instance.economic_exposure = ee_obj
                        fields_to_save.append('economic_exposure')
                    except Exception:
                        pass

                if fields_to_save:
                    instance.save(update_fields=fields_to_save)
            except Exception:
                pass

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='map-points')
    def map_points(self, request):
        """
        Ultra-lightweight endpoint returning only the fields needed for map markers.
        Strictly limited to India bounds to prevent global records from appearing.
        Fields: id, lat, lng, frp, predicted_class, source_type, processing_status, industrial_anomaly_status, confidence_score
        """
        limit = int(request.query_params.get('limit', 10000))
        
        from .models import IndiaBoundary
        boundary = IndiaBoundary.objects.first()
        
        # 1. Preliminary bounding box filter for speed
        india_qs = Hotspot.objects.filter(
            latitude__gte=6, latitude__lte=38,
            longitude__gte=68, longitude__lte=98,
            latitude__isnull=False, longitude__isnull=False
        )
        
        # 2. Strict spatial predicate (point-in-polygon)
        if boundary and boundary.geometry:
            india_qs = india_qs.filter(location__intersects=boundary.geometry)
            
        india_qs = india_qs.order_by('-frp')[:limit]
        
        # Select required fields
        fields = ['id', 'latitude', 'longitude', 'frp', 'predicted_class', 'source_type', 'processing_status', 'industrial_anomaly_status', 'confidence_score']
        india_data = list(india_qs.values(*fields))
        
        combined_data = []
        for item in india_data:
            # Rename keys to match expected output
            item['lat'] = item.pop('latitude')
            item['lng'] = item.pop('longitude')
            combined_data.append(item)
                
        return Response(combined_data)

    @action(detail=True, methods=['get'])
    def predict(self, request, pk=None):
        """Classification and SHAP explanation for a specific hotspot."""
        hotspot = self.get_object()
        return Response({
            'hotspot_id': hotspot.id,
            'predicted_class': hotspot.predicted_class,
            'confidence_score': hotspot.confidence_score,
            'shap_values': hotspot.shap_values
        })

    @action(detail=False, methods=['get'])
    def facilities(self, request):
        """Return all industrial facilities (max 10000) for map rendering."""
        from .models import FacilityCandidate
        from .serializers import FacilityCandidateSerializer
        facilities = FacilityCandidate.objects.filter(geometry__isnull=False)[:10000]
        serializer = FacilityCandidateSerializer(facilities, many=True)
        return Response(serializer.data)
