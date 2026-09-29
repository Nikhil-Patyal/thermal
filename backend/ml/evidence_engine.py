import pandas as pd
import numpy as np
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
        self._tree = None
        self._facilities = None

    def _init_facilities(self):
        if self._tree is None:
            facs = list(FacilityCandidate.objects.all())
            self._facilities = facs
            if not facs:
                self._tree = False # Mark as initialized but empty
                return
            
            coords = []
            for f in facs:
                if f.geometry:
                    coords.append((f.geometry.x, f.geometry.y))
                else:
                    coords.append((200, 200)) # Ignore out of bounds
                    
            from scipy.spatial import KDTree
            self._tree = KDTree(coords)

    def _check_facility_overlap(self, lon, lat, scan, track):
        self._init_facilities()
        if not self._facilities or self._tree is False:
            return None
            
        buffer_dist = max(scan * 1000, 375) if pd.notna(scan) else 1000
        deg_dist = buffer_dist / 111000.0
        
        # Query tree
        dists, idxs = self._tree.query((lon, lat), k=1, distance_upper_bound=deg_dist)
        
        if dists != float('inf'):
            fac = self._facilities[idxs]
            actual_dist = dists * 111000.0
            pixel_size = max(scan * 1000, 375) if pd.notna(scan) else 375
            match_type = 'overlap' if actual_dist <= (pixel_size / 2 + 500) else 'proximity'
            
            return {
                'match': match_type,
                'category': fac.category,
                'name': fac.name,
                'distance': int(actual_dist)
            }
            
        return None

    def _sample_landcover(self, lon, lat, scan, track):
        if not hasattr(self, 'sampler'):
            from ml.landcover import LandCoverSampler
            self.sampler = LandCoverSampler()
        
        return self.sampler.sample(lat, lon, scan, track)

    def generate_weak_labels(self, df):
        """
        Takes the feature dataframe and returns a DataFrame with competing-evidence classification applied.
        """
        results = []
        
        for idx, row in df.iterrows():
            evidence = []
            sources = []
            missing = []
            
            lon = row.get('lng') if 'lng' in row else row.get('longitude')
            lat = row.get('lat') if 'lat' in row else row.get('latitude')
            scan = row.get('scan')
            track = row.get('track')
            frp = row.get('frp')
            
            # Default values
            label = 'Unknown thermal anomaly'
            confidence_str = None
            attribution_status = None
            is_tentative = False
            
            fractions = None
            
            # 1. Check Industrial / Mining Infrastructure
            is_overlap = False
            fac_match = self._check_facility_overlap(lon, lat, scan, track) if pd.notna(lon) and pd.notna(lat) else None
            if fac_match:
                fac_cat = fac_match['category']
                is_overlap = (fac_match['match'] == 'overlap')
                dist_str = "Overlaps" if is_overlap else f"Within {fac_match['distance']}m of"
                
                evidence.append(f"{dist_str} {fac_cat} ('{fac_match['name']}')")
                sources.append("OSM_Facility")
                if is_overlap:
                    if fac_cat == 'Volcano':
                        label = 'Volcanic anomaly'
                    elif fac_cat == 'Oil & Gas / Refinery / LNG':
                        label = 'Petrochemical / Refinery-associated anomaly'
                    elif fac_cat == 'Thermal Power Plant':
                        label = 'Thermal Power Plant-associated anomaly'
                    elif fac_cat == 'Steel / Metallurgical' or 'Mine' in fac_cat:
                        label = 'Mining / smelter-associated thermal anomaly'
                    else:
                        label = 'Industrial-associated thermal anomaly'
                    confidence_str = 'Strong'
                else:
                    # Weak proximity match
                    if fac_cat == 'Volcano':
                        label = 'Volcanic anomaly'
                    elif fac_cat == 'Oil & Gas / Refinery / LNG':
                        label = 'Petrochemical / Refinery-associated anomaly'
                    elif fac_cat == 'Thermal Power Plant':
                        label = 'Thermal Power Plant-associated anomaly'
                    elif fac_cat == 'Steel / Metallurgical' or 'Mine' in fac_cat:
                        label = 'Mining / smelter-associated thermal anomaly'
                    else:
                        label = 'Industrial-associated thermal anomaly'
                    confidence_str = 'Low'
                    is_tentative = True
            else:
                missing.append("OSM_Facility_Match")

            # 2. Check Land Cover Context if not an industrial overlap OR if no facility match
            if not fac_match:
                lc_data = self._sample_landcover(lon, lat, scan, track)
                if lc_data is None or lc_data.get('valid_coverage', 0.0) < 0.80:
                    missing.append("Raster_LandCover")
                    # Secondary fallback: Use Overpass Landcover if available
                    n_frac = row.get('forest_fraction_1000m', 0.0)
                    c_frac = row.get('cropland_fraction_1000m', 0.0)
                    if pd.notna(n_frac) and pd.notna(c_frac) and (n_frac > 0 or c_frac > 0):
                        attribution_status = 'overpass_fallback'
                        if n_frac >= c_frac:
                            label = 'Likely wildland vegetation burning'
                            confidence_str = 'Moderate'
                            evidence.append("Raster missing. Overpass fallback: Forest/woodland area detected.")
                        else:
                            label = 'Likely agricultural burning'
                            confidence_str = 'Moderate'
                            evidence.append("Raster missing. Overpass fallback: Farmland area detected.")
                    else:
                        attribution_status = 'heuristic_fallback'
                        # Deterministic Fallback Heuristic using FRP
                        if frp and float(frp) > 10.0:
                            label = 'Likely wildland vegetation burning'
                            confidence_str = 'Low'
                            is_tentative = True
                            evidence.append(f"Landcover missing. Fallback: Moderate/High intensity (FRP {float(frp):.1f} MW) suggests wildland fire.")
                        else:
                            label = 'Likely agricultural burning'
                            confidence_str = 'Low'
                            is_tentative = True
                            frp_val = float(frp) if frp else 0.0
                            evidence.append(f"Landcover missing. Fallback: Low intensity (FRP {frp_val:.1f} MW) suggests agricultural burning.")
                else:
                    fractions = lc_data
                    v = lc_data.get('valid_coverage', 0.0)
                    c = lc_data.get('cropland_fraction', 0.0)
                    n = lc_data.get('tree_fraction', 0.0) + lc_data.get('shrub_fraction', 0.0) + lc_data.get('grass_fraction', 0.0)
                    
                    sources.append("LandCover")
                    # Strict Heuristic Baseline
                    if c >= 0.70 and n <= 0.20:
                        label = 'Likely agricultural burning'
                        confidence_str = 'Moderate'
                        evidence.append(f"Cropland dominates footprint (C={c*100:.1f}%, N={n*100:.1f}%)")
                    elif n >= 0.70 and c <= 0.20:
                        label = 'Likely wildland vegetation burning'
                        confidence_str = 'Moderate'
                        evidence.append(f"Natural vegetation dominates footprint (N={n*100:.1f}%, C={c*100:.1f}%)")
                    elif (c + n) >= 0.60 and (c - n) >= 0.20:
                        label = 'Likely agricultural burning'
                        confidence_str = 'Low'
                        is_tentative = True
                        evidence.append(f"Mixed landscape, crop support greater (C={c*100:.1f}%, N={n*100:.1f}%)")
                    elif (c + n) >= 0.60 and (n - c) >= 0.20:
                        label = 'Likely wildland vegetation burning'
                        confidence_str = 'Low'
                        is_tentative = True
                        evidence.append(f"Mixed landscape, natural support greater (N={n*100:.1f}%, C={c*100:.1f}%)")
                    else:
                        attribution_status = 'heuristic_fallback'
                        if frp and float(frp) > 10.0:
                            label = 'Likely wildland vegetation burning'
                            confidence_str = 'Low'
                            is_tentative = True
                            evidence.append(f"Mixed landcover (C={c*100:.0f}%, N={n*100:.0f}%). Fallback: FRP {float(frp):.1f}MW suggests wildland.")
                        else:
                            label = 'Likely agricultural burning'
                            confidence_str = 'Low'
                            is_tentative = True
                            frp_val = float(frp) if frp else 0.0
                            evidence.append(f"Mixed landcover (C={c*100:.0f}%, N={n*100:.0f}%). Fallback: FRP {frp_val:.1f}MW suggests agriculture.")
                            
            item_id = row.name if hasattr(row, 'name') and row.name is not None else row.get('id', idx)

            if is_tentative:
                label = f"{label} — tentative"

            results.append({
                'id': item_id,
                'label': label,
                'label_confidence_str': confidence_str,
                'label_evidence': evidence,
                'label_sources': list(set(sources)),
                'missing_sources': list(set(missing)),
                'attribution_status': attribution_status,
                'is_tentative': is_tentative,
                'fractions': fractions
            })
            
        df_res = pd.DataFrame(results)
        if 'id' in df_res.columns:
            df_res.set_index('id', inplace=True)
        return df_res
