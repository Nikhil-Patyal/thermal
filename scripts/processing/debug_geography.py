import os
import sys
import django
from pprint import pprint

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/backend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from geography.services import GeographyService

def run():
    # Test coordinates (e.g. Jharia coal field area: 23.74, 86.41)
    lat, lng = 23.74, 86.41
    print(f"Extracting features for {lat}, {lng}...")
    features = GeographyService.extract_context_features(lat, lng)
    pprint(features)

if __name__ == "__main__":
    run()
