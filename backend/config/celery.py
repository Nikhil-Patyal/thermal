import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module for 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')
# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# -------------------------------------------------------------------
# Periodic task schedule (Beat)
# -------------------------------------------------------------------
app.conf.beat_schedule = {
    'fetch-firms-every-hour': {
        'task': 'hotspots.tasks.fetch_live_firms_data',
        'schedule': crontab(minute=0, hour='*'),  # run at the top of each hour
    },
}

# Optional: enable UTC and set timezone
app.conf.timezone = 'UTC'
