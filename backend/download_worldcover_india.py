import os
import subprocess
import requests
from concurrent.futures import ThreadPoolExecutor

# India Bounding Box: ~6N to ~36N, ~66E to ~99E
lats = range(6, 39, 3)
lons = range(66, 102, 3)

out_dir = "data/worldcover"
os.makedirs(out_dir, exist_ok=True)

base_url = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map"

tiles_to_download = []
for lat in lats:
    for lon in lons:
        lat_str = f"N{lat:02d}" if lat >= 0 else f"S{abs(lat):02d}"
        lon_str = f"E{lon:03d}" if lon >= 0 else f"W{abs(lon):03d}"
        tile_name = f"ESA_WorldCover_10m_2021_v200_{lat_str}{lon_str}_Map.tif"
        tiles_to_download.append(tile_name)

def download_tile(tile_name):
    url = f"{base_url}/{tile_name}"
    out_path = os.path.join(out_dir, tile_name)
    if os.path.exists(out_path):
        return True
        
    try:
        resp = requests.head(url, timeout=10)
        if resp.status_code != 200:
            return False
            
        print(f"Downloading {tile_name}...")
        # Use stream to download
        with requests.get(url, stream=True, timeout=20) as r:
            r.raise_for_status()
            with open(out_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Finished {tile_name}")
        return True
    except Exception as e:
        print(f"Failed {tile_name}: {e}")
        return False

if __name__ == "__main__":
    print(f"Checking/Downloading {len(tiles_to_download)} tiles for India...")

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(download_tile, tiles_to_download))

    print("Downloads complete. Building VRT...")

    vrt_path = "data/worldcover_india.vrt"
    tif_files = [os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.endswith(".tif")]

    if tif_files:
        with open("data/tif_list.txt", "w") as f:
            for tif in tif_files:
                f.write(f"{tif}\n")
        
        # gdalbuildvrt stitches them together virtually (takes seconds, no data duplicated)
        subprocess.run(["gdalbuildvrt", "-input_file_list", "data/tif_list.txt", vrt_path], check=True)
        print(f"✅ Created virtual raster at {vrt_path}")
        print("Please update config/settings.py so WORLDCOVER_RASTER_PATH points to this file!")
    else:
        print("No TIF files downloaded.")
