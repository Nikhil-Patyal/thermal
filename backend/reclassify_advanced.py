import os
import django
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from hotspots.models import Hotspot
import random

hotspots = Hotspot.objects.select_related('population_exposure', 'economic_exposure', 'weather').all()
updated = 0

for hotspot in hotspots:
    frp = hotspot.frp or 0
    brightness = hotspot.brightness or 0
    
    pop_count = hotspot.population_exposure.population_count if hotspot.population_exposure and hotspot.population_exposure.population_count else 0
    gdp = hotspot.economic_exposure.gdp if hotspot.economic_exposure and hotspot.economic_exposure.gdp else 0
    temp = hotspot.weather.temperature_c if hotspot.weather and hotspot.weather.temperature_c else 20
    
    is_day = False
    if hotspot.acquisition_date:
        hour = hotspot.acquisition_date.hour
        is_day = 6 <= hour <= 18
        
    predicted_class = "unknown"
    
    if frp > 100 or brightness > 340:
        if pop_count > 10000 or gdp > 1e10:
            predicted_class = 'Industrial Fire'
        elif not is_day:
            predicted_class = 'Gas Flare'
        else:
            predicted_class = 'Wildfire / Forest Fire'
    elif frp > 30:
        if pop_count > 5000:
            predicted_class = 'Industrial Fire'
        elif temp > 30:
            predicted_class = 'Wildfire / Forest Fire'
        else:
            predicted_class = 'Agriculture Burning'
    else:
        if pop_count > 20000:
            predicted_class = 'Other Persistent Source'
        elif not is_day and brightness < 310:
            predicted_class = 'Mining & Smelter Thermal Activity'
        else:
            predicted_class = 'Agriculture Burning'
            
    hotspot.predicted_class = predicted_class
    updated += 1

Hotspot.objects.bulk_update(hotspots, ['predicted_class'], batch_size=2000)
print(f"Reclassified {updated} hotspots with advanced logic.")
