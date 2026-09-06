from django.db import models

class FirmsDetection(models.Model):
    # Match the database design in Section 9
    latitude = models.FloatField()
    longitude = models.FloatField()
    acq_date = models.DateField()
    acq_time = models.CharField(max_length=10) # Often stored as string like '0415' or TimeField
    frp = models.FloatField()
    brightness = models.FloatField(null=True, blank=True)
    bright_ti4 = models.FloatField(null=True, blank=True)
    bright_ti5 = models.FloatField(null=True, blank=True)
    confidence = models.CharField(max_length=20, null=True, blank=True)
    satellite = models.CharField(max_length=50)
    instrument = models.CharField(max_length=50)
    daynight = models.CharField(max_length=1, null=True, blank=True)
    
    # Removed GeoDjango spatial field
    
    raw_payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'firms_detections'
        indexes = [
            models.Index(fields=['acq_date']),
            models.Index(fields=['satellite', 'instrument']),
        ]

    def __str__(self):
        return f"{self.instrument} {self.satellite} Detection at {self.acq_date} {self.acq_time} (FRP: {self.frp})"
