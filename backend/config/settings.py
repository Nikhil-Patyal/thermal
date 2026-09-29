import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file if it exists
load_dotenv(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = 'django-insecure-dummy-key-for-agni-drishti'

DEBUG = True

GDAL_LIBRARY_PATH = '/Users/nikhilpatyal/miniforge3/lib/libgdal.dylib'
GEOS_LIBRARY_PATH = '/Users/nikhilpatyal/miniforge3/lib/libgeos_c.dylib'

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.gis',
    'rest_framework',
    'corsheaders',
    
    # AGNI-DRISHTI Apps
    'hotspots.apps.HotspotsConfig',
    'firms.apps.FirmsConfig',
    'thermal_sources.apps.ThermalSourcesConfig',
    'infrastructure.apps.InfrastructureConfig',
    'satellite_imagery.apps.SatelliteImageryConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

USE_SQLITE = os.getenv('USE_SQLITE', 'false').lower() == 'true'

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.spatialite',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    SPATIALITE_LIBRARY_PATH = '/Users/nikhilpatyal/miniforge3/lib/mod_spatialite.dylib'
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': os.getenv('POSTGRES_DB', 'agni_drishti'),
            'USER': os.getenv('POSTGRES_USER', 'agni_user'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'agni_password'),
            'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
            'OPTIONS': {
                'options': '-c max_parallel_workers_per_gather=0'
            }
        }
    }

# Cache – Redis for FIRMS responses
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = True  # For dev only

# -----------------------------------------------------------
# Media files (satellite imagery cache)
# -----------------------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# Sentinel Hub credentials (read from .env)
SENTINEL_HUB_CLIENT_ID = os.getenv('SENTINEL_HUB_CLIENT_ID', '')
SENTINEL_HUB_CLIENT_SECRET = os.getenv('SENTINEL_HUB_CLIENT_SECRET', '')
SENTINEL_HUB_TOKEN_URL = os.getenv('SENTINEL_HUB_TOKEN_URL', 'https://services.sentinel-hub.com/oauth/token')
SENTINEL_HUB_PROCESS_URL = os.getenv('SENTINEL_HUB_PROCESS_URL', 'https://services.sentinel-hub.com/api/v1/process')
# Directory where fetched satellite imagery tiles are cached (relative to MEDIA_ROOT)
SATELLITE_IMAGERY_CACHE_DIR = MEDIA_ROOT / 'satellite'
# Tuning parameters
SENTINEL_HUB_MAX_CLOUD = int(os.getenv('SENTINEL_HUB_MAX_CLOUD', '20'))  # % cloud coverage allowed
SENTINEL_HUB_OUTPUT_SIZE = int(os.getenv('SENTINEL_HUB_OUTPUT_SIZE', '256'))  # pixels (square)
SENTINEL_HUB_BBOX_RADIUS_KM = float(os.getenv('SENTINEL_HUB_BBOX_RADIUS_KM', 0.8))  # 0.8 km radius → 1.6 km × 1.6 km area
SENTINEL_HUB_DATE_RANGE_DAYS = int(os.getenv('SENTINEL_HUB_DATE_RANGE_DAYS', '1825'))  # days back from today (5 years)

# -----------------------------------------------------------
# Geography Context APIs (Copernicus & Overpass)
# -----------------------------------------------------------
COPERNICUS_API_KEY = os.getenv('COPERNICUS_API_KEY', '')
OVERPASS_ENDPOINT = os.getenv('OVERPASS_ENDPOINT', 'https://overpass-api.de/api/interpreter')

WORLDCOVER_RASTER_PATH = os.path.join(BASE_DIR, 'data/worldcover_india.vrt')
