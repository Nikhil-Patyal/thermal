from rest_framework import serializers
from .models import EnrichmentStatus, EvidenceRecord
from .models import (
    Hotspot, EconomicExposure, AirQuality, SafeRoute, 
    Weather, PopulationExposure, WaterQuality
)

class EconomicExposureSerializer(serializers.ModelSerializer):
    class Meta:
        model = EconomicExposure
        fields = '__all__'

class AirQualitySerializer(serializers.ModelSerializer):
    class Meta:
        model = AirQuality
        fields = '__all__'

class SafeRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafeRoute
        fields = '__all__'

class WeatherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Weather
        fields = '__all__'

class PopulationExposureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopulationExposure
        fields = '__all__'

class WaterQualitySerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterQuality
        fields = '__all__'

class HotspotSerializer(serializers.ModelSerializer):
    # Embed related evidence objects
    enrichment_status = serializers.SerializerMethodField()
    evidence_record = serializers.SerializerMethodField()
    economic_exposure = EconomicExposureSerializer(read_only=True)
    air_quality = AirQualitySerializer(read_only=True)
    safe_route = SafeRouteSerializer(read_only=True)
    weather = WeatherSerializer(read_only=True)
    population_exposure = PopulationExposureSerializer(read_only=True)
    water_quality = WaterQualitySerializer(read_only=True)
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()
    anomaly_score = serializers.SerializerMethodField()

    def get_lat(self, obj):
        return obj.latitude

    def get_lng(self, obj):
        return obj.longitude

    def get_anomaly_score(self, obj):
        try:
            return obj.shap_values.get('evidence', {}).get('anomaly_score')
        except Exception:
            return None

    def get_enrichment_status(self, obj):
        if obj.enrichment_status:
            return {
                "source": obj.enrichment_status.source_name,
                "status": obj.enrichment_status.status,
                "updated_at": obj.enrichment_status.updated_at,
            }
        return None

    def get_evidence_record(self, obj):
        if obj.evidence_record:
            return {
                "rule_id": obj.evidence_record.rule_id,
                "evidence": obj.evidence_record.evidence_text,
                "weight": obj.evidence_record.weight,
            }
        return None
        

    

    

    class Meta:
        model = Hotspot
        fields = [
            'id', 'frp', 'scan', 'confidence', 'brightness', 'acquisition_date',
            'lat', 'lng', 'anomaly_score', 'economic_exposure', 'air_quality', 'safe_route',
            'weather', 'population_exposure', 'water_quality',
            'predicted_class', 'confidence_score', 'shap_values', 'fetched_at',
            'label', 'label_type', 'label_confidence', 'label_evidence', 
            'label_sources', 'missing_sources', 'features',
            # New evidence fields
            'enrichment_status', 'evidence_record', 'source_context', 'thermal_behaviour',
            'industrial_subtype', 'decision_status', 'landcover_source', 'landcover_version',
            'osm_query_status', 'weather_status', 'population_status',
        ]




