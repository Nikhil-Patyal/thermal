import os
import pandas as pd
import argparse
from datetime import datetime

# NASA FIRMS Public 7-Day Global Active Fire URLs (No API Key Required)
# These files contain hundreds of thousands of real-time fire detections globally.
FIRMS_PUBLIC_VIIRS_7D = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_Global_7d.csv"
FIRMS_PUBLIC_MODIS_7D = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Global_7d.csv"

def fetch_live_firms_data(source='viirs'):
    """
    Downloads the massive 7-day global live dataset from NASA FIRMS.
    Returns the path to the saved CSV.
    """
    url = FIRMS_PUBLIC_VIIRS_7D if source == 'viirs' else FIRMS_PUBLIC_MODIS_7D
    print(f"\n[NASA FIRMS] Initiating live data fetch from:\n {url}")
    print("This is a massive dataset (7 days global). Please wait while it downloads...")
    
    try:
        df = pd.read_csv(url)
        print(f"[NASA FIRMS] Successfully downloaded {len(df):,} live fire records.")
        
        # Save raw data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, "../../data/raw")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f"firms_live_global_{source}_{timestamp}.csv")
        output_path = os.path.abspath(output_path)
        
        df.to_csv(output_path, index=False)
        print(f"[NASA FIRMS] Live data saved to: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"[ERROR] Failed to fetch live FIRMS data: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch 100,000+ live NASA FIRMS records.")
    parser.add_argument('--source', choices=['viirs', 'modis'], default='viirs')
    args = parser.parse_args()
    
    fetch_live_firms_data(args.source)
