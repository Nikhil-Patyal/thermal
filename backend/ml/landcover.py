import os
import math
import numpy as np
import pandas as pd
try:
    import rasterio
    from rasterio.windows import from_bounds
except ImportError:
    rasterio = None

from django.conf import settings

# ESA WorldCover 2021 Class Mapping
# 10: Tree cover
# 20: Shrubland
# 30: Grassland
# 40: Cropland
# 50: Built-up
# 60: Bare / sparse vegetation
# 70: Snow and ice
# 80: Permanent water bodies
# 90: Herbaceous wetland
# 95: Mangroves
# 100: Moss and lichen

CLASS_MAPPING = {
    10: 'tree',
    20: 'shrub',
    30: 'grass',
    40: 'cropland',
    50: 'other', # built-up
    60: 'other', # bare
    70: 'other', # snow
    80: 'other', # water
    90: 'other', # wetland
    95: 'other', # mangroves
    100: 'other' # moss
}

class LandCoverSampler:
    def __init__(self):
        self.raster_path = getattr(settings, 'WORLDCOVER_RASTER_PATH', None)
        self.src = None
        if self.raster_path and os.path.exists(self.raster_path) and rasterio:
            try:
                self.src = rasterio.open(self.raster_path)
            except Exception as e:
                print(f"Failed to open raster: {e}")

    def __del__(self):
        if self.src:
            self.src.close()

    def _estimate_footprint_bounds(self, lat, lng, scan, track):
        """
        Estimate the bounding box of the footprint in degrees.
        VIIRS scan/track are in km. Default to 375m if missing.
        """
        # Convert km to meters. Default 375m
        scan_m = max(scan * 1000, 375) if pd.notna(scan) else 375
        track_m = max(track * 1000, 375) if pd.notna(track) else 375
        
        # 1 degree lat ~ 111,320 meters
        lat_offset = (track_m / 2) / 111320.0
        # 1 degree lng ~ 111,320 * cos(lat) meters
        lng_offset = (scan_m / 2) / (111320.0 * math.cos(math.radians(lat)))

        min_lat = lat - lat_offset
        max_lat = lat + lat_offset
        min_lng = lng - lng_offset
        max_lng = lng + lng_offset

        return min_lng, min_lat, max_lng, max_lat, f"{scan_m}mx{track_m}m"

    def sample(self, lat, lng, scan, track):
        """
        Sample the land cover fractions for a given footprint.
        Returns a dictionary of fractions, valid_coverage, and metadata.
        """
        if pd.isna(lat) or pd.isna(lng):
            return None
            
        min_lng, min_lat, max_lng, max_lat, footprint_method = self._estimate_footprint_bounds(lat, lng, scan, track)

        if not self.src:
            # D. For unavailable land-cover evidence, retry using another appropriate real source.
            # Since no fallback API is currently implemented/available locally, we safely report failure
            # without inventing fractions, recording provenance explicitly.
            return {
                'cropland_fraction': 0.0,
                'tree_fraction': 0.0,
                'shrub_fraction': 0.0,
                'grass_fraction': 0.0,
                'other_fraction': 0.0,
                'valid_coverage': 0.0,
                'footprint_method': footprint_method,
                'landcover_source': 'missing_raster_no_fallback',
                'landcover_version': 'none'
            }

        try:
            window = from_bounds(min_lng, min_lat, max_lng, max_lat, transform=self.src.transform)
            
            # Read the data for the window
            data = self.src.read(1, window=window)
            
            if data.size == 0:
                return None
                
            # Count pixels
            unique, counts = np.unique(data, return_counts=True)
            pixel_counts = dict(zip(unique, counts))
            
            total_pixels = data.size
            # Assuming 0 is nodata
            nodata_pixels = pixel_counts.get(0, 0)
            valid_pixels = total_pixels - nodata_pixels
            
            if total_pixels == 0:
                return None
                
            valid_coverage = valid_pixels / total_pixels

            if valid_pixels == 0:
                return {
                    'cropland_fraction': 0.0,
                    'tree_fraction': 0.0,
                    'shrub_fraction': 0.0,
                    'grass_fraction': 0.0,
                    'other_fraction': 0.0,
                    'valid_coverage': 0.0,
                    'footprint_method': footprint_method,
                    'landcover_source': 'ESA_WorldCover_2021',
                    'landcover_version': 'v200'
                }
            
            fractions = {
                'cropland': 0,
                'tree': 0,
                'shrub': 0,
                'grass': 0,
                'other': 0
            }
            
            for val, count in pixel_counts.items():
                if val == 0:
                    continue
                mapped_cat = CLASS_MAPPING.get(val, 'other')
                fractions[mapped_cat] += count
                
            return {
                'cropland_fraction': fractions['cropland'] / valid_pixels,
                'tree_fraction': fractions['tree'] / valid_pixels,
                'shrub_fraction': fractions['shrub'] / valid_pixels,
                'grass_fraction': fractions['grass'] / valid_pixels,
                'other_fraction': fractions['other'] / valid_pixels,
                'valid_coverage': valid_coverage,
                'footprint_method': footprint_method,
                'landcover_source': 'ESA_WorldCover_2021',
                'landcover_version': 'v200'
            }
        except Exception as e:
            print(f"Error sampling raster: {e}")
            return None
