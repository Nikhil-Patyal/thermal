from django.db import models

class ThermalSource(models.Model):
    source_id = models.CharField(max_length=50, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    first_detected = models.DateTimeField()
    last_detected = models.DateTimeField()
    detection_count = models.IntegerField()
    
    # FRP stats
    mean_frp = models.FloatField()
    median_frp = models.FloatField()
    max_frp = models.FloatField()
    min_frp = models.FloatField()
    frp_std = models.FloatField(null=True, blank=True)
    
    persistence = models.FloatField() # e.g. % of days active
    
    # ML Classification
    classification = models.CharField(max_length=100, default='UNKNOWN')
    confidence = models.FloatField(null=True, blank=True)
    anomaly_score = models.FloatField(null=True, blank=True)
    risk_score = models.FloatField(null=True, blank=True)
    
    status = models.CharField(max_length=50, default='NORMAL')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'thermal_sources'

    def __str__(self):
        return f"Thermal Source {self.source_id} ({self.classification})"
