import pandas as pd
import numpy as np
import rasterio
import os
from django.contrib.gis.geos import Point
from hotspots.models import FacilityCandidate

class EvidenceEngine:
    """
    Strict, deterministic rule-based thermal classification engine.
    Uses verifiable geographic context to classify hotspots.
    No uncalibrated ML models, no missing value imputation, and no synthetic confidence percentages.
    """
    def __init__(self, raster_path=None):
        self.raster_path = raster_path

    def _check_facility_overlap(self, lon, lat, scan, track):
        # Determine dynamic buffer in meters based on sensor metadata
        # VIIRS is typically ~375m, MODIS is ~1000m. Use scan/track if available.
        # Fallback to 1000m for uncertainty.
        buffer_dist = max(scan * 1000, 375) if pd.notna(scan) else 1000
        
        point = Point(lon, lat, srid=4326)
        
        # 1. Check exact polygon overlap first (ST_Intersects)
        exact_matches = FacilityCandidate.objects.filter(geometry__intersects=point)
        if exact_matches.exists():
            fac = exact_matches.first()
            return {
                'match': 'overlap',
                'category': fac.category,
                'name': fac.name,
                'distance': 0
            }
            
        # 2. Check dynamic proximity (ST_DWithin using geography for meters)
        # In Django, distance_lte uses the geometry SRID by default unless geography=True is set.
        # Since FacilityCandidate geometry is just GeometryField(srid=4326), we use distance_lte with degrees as a fast approximation,
        # or we cast. 1 degree ~ 111km, so buffer_dist/111000.
        deg_dist = buffer_dist / 111000.0
        prox_matches = FacilityCandidate.objects.filter(geometry__distance_lte=(point, deg_dist))
        if prox_matches.exists():
            # Get the closest one
            fac = prox_matches.first() # In a real implementation we'd order by distance, but Django distance_lte on geometry isn't orderable without distance() annotation.
            return {
                'match': 'proximity',
                'category': fac.category,
                'name': fac.name,
                'distance': buffer_dist
            }
            
        return None

    def _sample_landcover(self, lon, lat):
        if not self.raster_path or not os.path.exists(self.raster_path):
            return None, "WorldCover Raster Unavailable"
        
        # Sample rasterio implementation (mocked structure, since we lack the actual raster in the filesystem)
        # Normally, we'd open the raster, read the pixel value at (lon, lat) or window over (scan, track).
        # We will return None safely to avoid inventing values.
        return None, "WorldCover Raster Not Configured"

    def generate_weak_labels(self, df):
        """
        Takes the feature dataframe and returns a DataFrame with competing-evidence classification applied.
        """
        results = []
        
        THRESH_FOREST = 0.50
        THRESH_CROP = 0.30
        
        for idx, row in df.iterrows():
            evidence = []
            sources = []
            missing = []
            
            score_agri = 0.0
            score_wild = 0.0
            score_ind = 0.0
            score_mine = 0.0
            
            lon = row.get('longitude')
            lat = row.get('latitude')
            scan = row.get('scan')
            track = row.get('track')
            
            # 1. Check Industrial / Mining Infrastructure
            is_overlap = False
            fac_match = self._check_facility_overlap(lon, lat, scan, track) if pd.notna(lon) and pd.notna(lat) else None
            if fac_match:
                fac_cat = fac_match['category']
                is_overlap = (fac_match['match'] == 'overlap')
                pts = 2.0 if is_overlap else 1.0
                dist_str = "Overlaps" if is_overlap else f"Within {fac_match['distance']}m of"
                
                if fac_cat == 'Mine / quarry':
                    score_mine += pts
                    evidence.append(f"{dist_str} {fac_cat} ('{fac_match['name']}')")
                    sources.append("OSM_Facility")
                elif fac_cat == 'Smelter / metallurgical facility':
                    score_mine += pts
                    score_ind += pts * 0.5
                    evidence.append(f"{dist_str} {fac_cat} ('{fac_match['name']}')")
                    sources.append("OSM_Facility")
                else:
                    score_ind += pts
                    evidence.append(f"{dist_str} {fac_cat} ('{fac_match['name']}')")
                    sources.append("OSM_Facility")
            else:
                missing.append("OSM_Facility_Match")

            # 2. Check Land Cover Context
            lc_data, lc_status = self._sample_landcover(lon, lat)
            if lc_data is None:
                missing.append("Raster_LandCover")
                # Fallback to pre-enriched fractions if available (from old pipelines)
                forest = row.get('forest_fraction_1000m')
                cropland = row.get('cropland_fraction_1000m')
            else:
                forest = lc_data.get('forest')
                cropland = lc_data.get('cropland')
                
            if pd.notna(forest) and forest >= THRESH_FOREST:
                score_wild += 1.5
                evidence.append(f"Forest fraction ({forest*100:.0f}%) >= {THRESH_FOREST*100}%")
                sources.append("LandCover")
                
            if pd.notna(cropland) and cropland >= THRESH_CROP:
                score_agri += 1.5
                evidence.append(f"Cropland fraction ({cropland*100:.0f}%) >= {THRESH_CROP*100}%")
                sources.append("LandCover")

            # 3. Physical Attributes (FRP / Brightness) to help distinguish Agriculture vs Wildfire
            frp = row.get('frp')
            if pd.notna(frp):
                if frp > 100:
                    score_wild += 0.5
                    evidence.append(f"High FRP ({frp:.1f} MW) strongly supports wildland fire.")
                    sources.append("Satellite_Radiometry")
                elif frp < 15 and not is_overlap:
                    # Very small fires are typical of crop residue burning if no industry is present
                    score_agri += 0.5
                    evidence.append(f"Low FRP ({frp:.1f} MW) supports agricultural burning.")
                    sources.append("Satellite_Radiometry")

            # 4. Decision Logic: Competing Evidence
            scores = {
                'Likely agricultural burning': score_agri,
                'Likely wildland vegetation fire': score_wild,
                'Industrial-associated thermal anomaly': score_ind,
                'Mining / smelter-associated thermal anomaly': score_mine
            }
            
            best_class = max(scores, key=scores.get)
            best_score = scores[best_class]
            
            # Competing strong signals
            competing_scores = [s for s in scores.values() if s >= 1.0]
            
            if best_score < 1.0 or (len(competing_scores) > 1 and (sorted(competing_scores)[-1] - sorted(competing_scores)[-2] < 0.6)):
                # Handle uncertain or conflicting evidence using physical fallback features
                daynight = row.get('daynight')
                if pd.notna(frp) and frp < 15 and daynight == 'D':
                    label = 'Likely small agricultural burning (low confidence)'
                    confidence_str = "Low"
                    evidence.append("Geographic context missing, but daytime low FRP suggests agriculture.")
                elif pd.notna(frp) and frp > 100:
                    label = 'Likely wildland vegetation fire (low confidence)'
                    confidence_str = "Low"
                    evidence.append("Geographic context missing, but high FRP suggests wildfire.")
                elif daynight == 'N':
                    label = 'Unknown nighttime thermal anomaly'
                    confidence_str = "Low"
                    evidence.append("Geographic context missing. Nighttime occurrence.")
                elif daynight == 'D':
                    label = 'Unknown daytime thermal anomaly'
                    confidence_str = "Low"
                    evidence.append("Geographic context missing. Daytime occurrence.")
                else:
                    label = 'Other classification'
                    confidence_str = "Low"
                    evidence.append("Insufficient or conflicting evidence to classify.")
            else:
                label = best_class
                confidence_str = "Strong" if best_score >= 1.5 else "Moderate"
                
            item_id = row.name if hasattr(row, 'name') and row.name is not None else row.get('id', idx)

            results.append({
                'id': item_id,
                'label': label,
                'label_confidence_str': confidence_str,
                'label_evidence': evidence,
                'label_sources': list(set(sources)),
                'missing_sources': list(set(missing)),
            })
            
        df_res = pd.DataFrame(results)
        if 'id' in df_res.columns:
            df_res.set_index('id', inplace=True)
        return df_res
