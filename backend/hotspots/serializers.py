from rest_framework import serializers
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
    economic_exposure = EconomicExposureSerializer(read_only=True)
    air_quality = AirQualitySerializer(read_only=True)
    safe_route = SafeRouteSerializer(read_only=True)
    weather = WeatherSerializer(read_only=True)
    population_exposure = PopulationExposureSerializer(read_only=True)
    water_quality = WaterQualitySerializer(read_only=True)

    class Meta:
        model = Hotspot
        fields = [
            'id', 'frp', 'scan', 'confidence', 'brightness', 'acquisition_date',
            'location', 'economic_exposure', 'air_quality', 'safe_route',
            'weather', 'population_exposure', 'water_quality',
            'predicted_class', 'confidence_score', 'shap_values', 'fetched_at'
        ]
