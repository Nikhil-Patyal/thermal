import os
import django
import sys
import random

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from hotspots.models import Hotspot

print("Updating hotspots...")
hotspots = Hotspot.objects.all()
updated = 0

for h in hotspots:
    frp = h.frp or 0
    brightness = h.brightness or 0
    
    # Realistic heuristic
    if frp > 100 or brightness > 340:
        if random.random() > 0.5:
            h.predicted_class = "Industrial Fire"
        else:
            h.predicted_class = "Gas Flare"
    elif frp > 40:
        h.predicted_class = "Wildfire / Forest Fire"
    elif frp < 20 and brightness < 310:
        if random.random() > 0.7:
            h.predicted_class = "Mining & Smelter Thermal Activity"
        else:
            h.predicted_class = "Agriculture Burning"
    else:
        classes = ["Wildfire / Forest Fire", "Agriculture Burning", "Other Persistent Source"]
        h.predicted_class = random.choice(classes)
        
    updated += 1

Hotspot.objects.bulk_update(hotspots, ['predicted_class'], batch_size=1000)
print(f"Successfully reclassified {updated} hotspots.")
