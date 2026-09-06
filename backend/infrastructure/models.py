from django.db import models

class Infrastructure(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=100) # e.g. refinery, power_plant, mine
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Removed GeometryField
    
    source = models.CharField(max_length=100) # e.g. OSM, GEM
    external_id = models.CharField(max_length=100, null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'infrastructure'

    def __str__(self):
        return f"{self.type} - {self.name or self.external_id}"
