import requests
import csv
import os

def fetch_overpass_data():
    print("Fetching data from Overpass API...")
    # Bounding box for East India (Jharkhand, Odisha, West Bengal - known for mining and industry)
    # south, west, north, east
    bbox = "20.0, 84.0, 24.0, 88.0"
    
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json][timeout:60];
    (
      node["landuse"="industrial"]({bbox});
      way["landuse"="industrial"]({bbox});
      rel["landuse"="industrial"]({bbox});
      node["industrial"="mine"]({bbox});
      way["industrial"="mine"]({bbox});
      rel["industrial"="mine"]({bbox});
    );
    out center;
    """
    
    response = requests.post(overpass_url, data={'data': overpass_query}, headers={'User-Agent': 'ThermalSentinelDataFetcher/1.0'})
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}")
        print(response.text)
        return
        
    data = response.json()
    
    filepath = os.path.join(os.path.dirname(__file__), '../../backend/data/industrial_and_mines_data.csv')
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    count = 0
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Name', 'Category', 'Latitude', 'Longitude'])
        
        for element in data['elements']:
            lat = element.get('lat')
            lon = element.get('lon')
            if 'center' in element:
                lat = element['center']['lat']
                lon = element['center']['lon']
                
            if lat is None or lon is None:
                continue
                
            tags = element.get('tags', {})
            name = tags.get('name', 'Unknown Facility')
            
            category = 'Industrial'
            if tags.get('industrial') == 'mine':
                category = 'Mine'
                
            writer.writerow([name, category, lat, lon])
            count += 1
            
    print(f"Successfully wrote {count} records to {filepath}")

if __name__ == "__main__":
    fetch_overpass_data()
