import os
import django
import requests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

bbox = "18,72,19,73"
query = f"""
[out:json][timeout:25];
(
  node["landuse"="industrial"]({bbox});
  way["landuse"="industrial"]({bbox});
  node["man_made"~"works|chimney"]({bbox});
  node["industrial"~"refinery|oil|gas|petrochemical|smelter|metallurgical|steel"]({bbox});
  node["pipeline"="flare"]({bbox});
  node["substance"~"lng"]({bbox});
  node["power"="plant"]["generator:source"~"coal|gas|oil"]({bbox});
  node["landuse"="quarry"]({bbox});
  node["industrial"="mine"]({bbox});
  way["industrial"="mine"]({bbox});
  way["landuse"="quarry"]({bbox});
);
out center tags;
"""
res = requests.post("https://overpass-api.de/api/interpreter", data={'data': query}, timeout=30)
print(res.status_code, res.text)
