import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
settings.CELERY_TASK_ALWAYS_EAGER = True
settings.CELERY_TASK_EAGER_PROPAGATES = True

from hotspots.models import Hotspot
from hotspots.tasks import fetch_live_firms_data

def run_fetch():
    print("Clearing existing hotspots...")
    Hotspot.objects.all().delete()
    print("Fetching live FIRMS data (this may take a few minutes)...")
    fetch_live_firms_data()
    print(f"Fetch completed. Total hotspots: {Hotspot.objects.count()}")

if __name__ == '__main__':
    run_fetch()
