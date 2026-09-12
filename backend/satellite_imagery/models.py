from django.db import models

class ImageryCache(models.Model):
    hotspot_id = models.IntegerField(db_index=True)
    true_color_url = models.CharField(max_length=500, null=True, blank=True)
    false_color_url = models.CharField(max_length=500, null=True, blank=True)
    ndvi_url = models.CharField(max_length=500, null=True, blank=True)
    nbr_url = models.CharField(max_length=500, null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fetched_at']
