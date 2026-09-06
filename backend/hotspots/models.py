from django.contrib.gis.db import models as gis_models
from django.db import models

class EconomicExposure(models.Model):
    gdp = models.FloatField(null=True, blank=True)
    industrial_output = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"EconomicExposure(gdp={self.gdp})"

class AirQuality(models.Model):
    pm25 = models.FloatField(null=True, blank=True)
    no2 = models.FloatField(null=True, blank=True)
    aqi = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"AirQuality(PM2.5={self.pm25})"

class SafeRoute(models.Model):
    distance_km = models.FloatField(null=True, blank=True)
    travel_time_min = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"SafeRoute(dist={self.distance_km}km)"

class Weather(models.Model):
    temperature_c = models.FloatField(null=True, blank=True)
    wind_speed_ms = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"Weather(temp={self.temperature_c}C)"

class PopulationExposure(models.Model):
    population_count = models.BigIntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"PopulationExposure(count={self.population_count})"

class WaterQuality(models.Model):
    contamination_index = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"WaterQuality(index={self.contamination_index})"

class Hotspot(gis_models.Model):
    # FIRMS fields
    frp = models.FloatField(null=True, blank=True)
    scan = models.CharField(max_length=20, null=True, blank=True)
    confidence = models.IntegerField(null=True, blank=True)
    brightness = models.FloatField(null=True, blank=True)
    acquisition_date = models.DateTimeField(null=True, blank=True)
    
    # Geometry
    location = gis_models.PointField(geography=True, srid=4326)
    
    # Enrichment foreign keys
    economic_exposure = models.ForeignKey(EconomicExposure, on_delete=models.SET_NULL, null=True, blank=True)
    air_quality = models.ForeignKey(AirQuality, on_delete=models.SET_NULL, null=True, blank=True)
    safe_route = models.ForeignKey(SafeRoute, on_delete=models.SET_NULL, null=True, blank=True)
    weather = models.ForeignKey(Weather, on_delete=models.SET_NULL, null=True, blank=True)
    population_exposure = models.ForeignKey(PopulationExposure, on_delete=models.SET_NULL, null=True, blank=True)
    water_quality = models.ForeignKey(WaterQuality, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Classification fields
    predicted_class = models.CharField(max_length=50, null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)  # 0‑1
    shap_values = models.JSONField(null=True, blank=True)  # store SHAP explanation
    
    # Ingestion metadata
    fetched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Hotspot(id={self.id}, class={self.predicted_class})"
