# GIS import removed – using plain Django models
from django.db import models
from django.contrib.gis.db import models as gis_models

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

class IndiaBoundary(models.Model):
    name = models.CharField(max_length=100, default='India')
    geometry = gis_models.MultiPolygonField(srid=4326)
    source = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return self.name

class FacilityCandidate(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    geometry = gis_models.GeometryField(srid=4326, null=True, blank=True)
    distance_km = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"FacilityCandidate(name={self.name})"

class WorldCoverTile(models.Model):
    tile_id = models.CharField(max_length=50, null=True, blank=True)
    land_cover_class = models.CharField(max_length=100, null=True, blank=True)
    tree_cover = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"WorldCoverTile(tile_id={self.tile_id})"

class ModelVersion(models.Model):
    version_string = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ModelVersion(version={self.version_string})"

class Hotspot(gis_models.Model):
    # FIRMS fields
    frp = models.FloatField(null=True, blank=True)
    scan = models.FloatField(null=True, blank=True)
    track = models.FloatField(null=True, blank=True)
    confidence = models.IntegerField(null=True, blank=True)
    
    # Generic brightness (used loosely by old logic, kept for backward compat)
    brightness = models.FloatField(null=True, blank=True)
    
    # Specific brightness bands
    bright_ti4 = models.FloatField(null=True, blank=True)
    bright_ti5 = models.FloatField(null=True, blank=True)
    bright_t31 = models.FloatField(null=True, blank=True)
    
    # Sensor metadata
    instrument = models.CharField(max_length=50, null=True, blank=True)
    satellite = models.CharField(max_length=50, null=True, blank=True)
    daynight = models.CharField(max_length=10, null=True, blank=True)
    version = models.CharField(max_length=50, null=True, blank=True)
    
    acquisition_date = models.DateTimeField(null=True, blank=True)
    
    # Geometry
    location = gis_models.PointField(geography=True, srid=4326, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Enrichment foreign keys
    economic_exposure = models.ForeignKey(EconomicExposure, on_delete=models.SET_NULL, null=True, blank=True)
    air_quality = models.ForeignKey(AirQuality, on_delete=models.SET_NULL, null=True, blank=True)
    safe_route = models.ForeignKey(SafeRoute, on_delete=models.SET_NULL, null=True, blank=True)
    weather = models.ForeignKey(Weather, on_delete=models.SET_NULL, null=True, blank=True)
    population_exposure = models.ForeignKey(PopulationExposure, on_delete=models.SET_NULL, null=True, blank=True)
    water_quality = models.ForeignKey(WaterQuality, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Additional foreign keys
    facility_candidate = models.ForeignKey(FacilityCandidate, on_delete=models.SET_NULL, null=True, blank=True)
    world_cover_tile = models.ForeignKey(WorldCoverTile, on_delete=models.SET_NULL, null=True, blank=True)
    model_version = models.ForeignKey(ModelVersion, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Classification fields
    predicted_class = models.CharField(max_length=50, null=True, blank=True)  # Legacy combined field
    confidence_score = models.CharField(max_length=20, null=True, blank=True)  # Low/Moderate/Strong
    shap_values = models.JSONField(null=True, blank=True)  # store SHAP explanation
    
    # Normalized classification fields
    PROCESSING_CHOICES = [
        ('PENDING', 'Pending enrichment'),
        ('PARTIAL', 'Partial evidence'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed processing')
    ]
    processing_status = models.CharField(max_length=20, choices=PROCESSING_CHOICES, default='PENDING')
    source_type = models.CharField(max_length=100, null=True, blank=True)
    industrial_anomaly_status = models.CharField(max_length=100, null=True, blank=True)
    
    # Evidence Engine & Label Provenance (Weak Labels)
    label = models.CharField(max_length=50, null=True, blank=True)
    label_type = models.CharField(max_length=20, null=True, blank=True) # e.g. "weak", "ground_truth"
    label_confidence = models.CharField(max_length=20, null=True, blank=True)
    label_evidence = models.JSONField(null=True, blank=True) # List of evidence strings
    label_sources = models.JSONField(null=True, blank=True) # List of sources
    missing_sources = models.JSONField(null=True, blank=True) # List of missing source names
    # Enriched feature vector (JSONB)
    features = models.JSONField(null=True, blank=True)
    # New evidence and provenance fields
    enrichment_status = models.ForeignKey('EnrichmentStatus', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    evidence_record = models.ForeignKey('EvidenceRecord', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    source_context = models.CharField(max_length=50, null=True, blank=True)
    thermal_behaviour = models.CharField(max_length=50, null=True, blank=True)
    industrial_subtype = models.CharField(max_length=50, null=True, blank=True)
    decision_status = models.CharField(max_length=30, null=True, blank=True)
    # Provenance fields
    landcover_source = models.CharField(max_length=100, null=True, blank=True)
    landcover_version = models.CharField(max_length=20, null=True, blank=True)
    footprint_method = models.CharField(max_length=50, null=True, blank=True)
    osm_query_status = models.CharField(max_length=30, null=True, blank=True)
    weather_status = models.CharField(max_length=30, null=True, blank=True)
    population_status = models.CharField(max_length=30, null=True, blank=True)
    
    # Detailed Land Cover Fractions (WorldCover 10m)
    cropland_fraction = models.FloatField(null=True, blank=True)
    tree_fraction = models.FloatField(null=True, blank=True)
    shrub_fraction = models.FloatField(null=True, blank=True)
    grass_fraction = models.FloatField(null=True, blank=True)
    other_fraction = models.FloatField(null=True, blank=True)
    valid_coverage = models.FloatField(null=True, blank=True)
    
    attribution_status = models.CharField(max_length=100, null=True, blank=True)
    evidence_strength = models.CharField(max_length=50, null=True, blank=True)
    is_tentative = models.BooleanField(default=False)
    
    # Additional fields
    risk_score = models.FloatField(null=True, blank=True)
    severity = models.CharField(max_length=50, null=True, blank=True)
    
    # Ingestion metadata
    fetched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Hotspot(id={self.id}, class={self.predicted_class})"

class EnrichmentStatus(models.Model):
    hotspot = models.ForeignKey(Hotspot, on_delete=models.CASCADE, related_name='enrichment_statuses')
    source_name = models.CharField(max_length=100)
    status = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"EnrichmentStatus(hotspot={self.hotspot_id}, source={self.source_name})"

class EvidenceRecord(models.Model):
    hotspot = models.ForeignKey(Hotspot, on_delete=models.CASCADE, related_name='evidence_records')
    rule_id = models.CharField(max_length=100, null=True, blank=True)
    evidence_text = models.TextField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"EvidenceRecord(hotspot={self.hotspot_id}, rule={self.rule_id})"

class EnrichmentLog(models.Model):
    hotspot = models.ForeignKey(Hotspot, on_delete=models.CASCADE)
    source_name = models.CharField(max_length=100)
    query_timestamp = models.DateTimeField()
    available = models.BooleanField()
    details = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"EnrichmentLog(hotspot={self.hotspot_id}, source={self.source_name})"
