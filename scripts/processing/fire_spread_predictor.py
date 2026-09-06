"""
AGNI-DRISHTI: AI Fire Spread Predictor
=======================================
Predicts fire spread over time using wind, vegetation, terrain, 
and historical pattern analysis:
  - Wind-driven spread vector model
  - Vegetation fuel density influence
  - Terrain slope/aspect acceleration
  - Outputs predicted danger zones at T+1h, T+3h, T+6h, T+12h
"""

import numpy as np
import warnings
warnings.filterwarnings('ignore')


# ── Environmental Constants ──────────────────────────────────────

SPREAD_RATE_BASE_KMH = {
    0: 3.5,   # Wildfire — fast spreading
    1: 0.2,   # Industrial — minimal spread
    2: 0.0,   # Gas Flare — no spread
    3: 1.5,   # Agriculture — moderate
    4: 0.05,  # Mining — negligible spread
}

VEGETATION_MULTIPLIER = {
    'dense_forest': 2.5,
    'open_forest': 1.8,
    'scrubland': 1.4,
    'grassland': 2.0,
    'cropland': 1.6,
    'urban': 0.3,
    'barren': 0.1,
    'water': 0.0,
}


class FireSpreadPredictor:
    """
    AI-powered fire spread prediction model.
    Uses a simplified Rothermel-inspired model combined with 
    wind vectors and terrain effects.
    """
    
    def __init__(self):
        self.time_horizons = [1, 3, 6, 12]  # hours
    
    def predict_spread(self, event_data):
        """
        Predict fire spread for a single thermal event.
        
        Returns:
            dict with spread predictions at each time horizon
        """
        target_class = event_data.get('target_class', 0)
        frp = event_data.get('frp', 30)
        lat = event_data.get('lat', 22.0)
        lng = event_data.get('lng', 78.0)
        
        base_rate = SPREAD_RATE_BASE_KMH.get(target_class, 0.5)
        
        # If non-spreading source, return minimal predictions
        if base_rate < 0.1:
            return self._no_spread_prediction(lat, lng, target_class)
        
        # Simulate environmental factors
        wind_speed, wind_direction = self._simulate_wind(lat, lng)
        veg_type, veg_multiplier = self._simulate_vegetation(lat, lng)
        slope_factor = self._simulate_terrain(lat, lng)
        
        # FRP intensity factor (higher FRP = faster spread)
        intensity_factor = np.clip(frp / 50.0, 0.5, 3.0)
        
        # Effective spread rate
        effective_rate = base_rate * veg_multiplier * slope_factor * intensity_factor
        
        # Wind enhancement (fire spreads faster downwind)
        wind_boost = 1.0 + (wind_speed / 30.0) * 0.8  # up to 80% boost from wind
        
        predictions = {}
        for t_hours in self.time_horizons:
            radius_km = effective_rate * wind_boost * t_hours
            
            # Generate elliptical spread (elongated in wind direction)
            ellipse = self._compute_spread_ellipse(
                lat, lng, radius_km, wind_direction, wind_speed, t_hours
            )
            
            # Compute impact metrics
            area_sq_km = np.pi * ellipse['semi_major'] * ellipse['semi_minor']
            
            predictions[f"t_plus_{t_hours}h"] = {
                'radius_km': round(radius_km, 2),
                'semi_major_km': round(ellipse['semi_major'], 2),
                'semi_minor_km': round(ellipse['semi_minor'], 2),
                'direction_deg': round(ellipse['direction'], 1),
                'area_sq_km': round(area_sq_km, 2),
                'confidence': round(max(0.3, 0.95 - 0.05 * t_hours), 2),
                'boundary_points': ellipse['boundary_points'],
            }
        
        return {
            'predictions': predictions,
            'wind_speed_kmh': round(wind_speed, 1),
            'wind_direction_deg': round(wind_direction, 1),
            'vegetation_type': veg_type,
            'effective_spread_rate_kmh': round(effective_rate, 2),
            'spread_risk': self._classify_spread_risk(effective_rate),
            'is_spreading': True,
        }
    
    def _no_spread_prediction(self, lat, lng, target_class):
        """Return predictions for non-spreading sources."""
        class_names = {1: 'Industrial', 2: 'Gas Flare', 4: 'Mining'}
        return {
            'predictions': {f"t_plus_{t}h": {
                'radius_km': 0.0,
                'semi_major_km': 0.0,
                'semi_minor_km': 0.0,
                'direction_deg': 0,
                'area_sq_km': 0.0,
                'confidence': 0.99,
                'boundary_points': [],
            } for t in self.time_horizons},
            'wind_speed_kmh': 0,
            'wind_direction_deg': 0,
            'vegetation_type': 'N/A',
            'effective_spread_rate_kmh': 0.0,
            'spread_risk': 'NONE',
            'is_spreading': False,
            'note': f'{class_names.get(target_class, "Source")} — Stationary heat source, no fire spread expected.'
        }
    
    def _simulate_wind(self, lat, lng):
        """Simulate wind conditions based on location."""
        # Simulated seasonal wind patterns for India
        np.random.seed(int(abs(lat * 1000 + lng * 100)) % 2**31)
        base_speed = np.random.uniform(5, 35)  # km/h
        direction = np.random.uniform(0, 360)  # degrees from North
        
        # Add some turbulence
        speed = base_speed + np.random.normal(0, 3)
        speed = max(0, speed)
        
        return speed, direction
    
    def _simulate_vegetation(self, lat, lng):
        """Simulate vegetation type based on coordinates."""
        np.random.seed(int(abs(lat * 1000 + lng * 100)) % 2**31)
        
        # Simplified India vegetation zones
        if lat > 28:  # Northern mountains
            veg_type = np.random.choice(['dense_forest', 'open_forest', 'scrubland'], p=[0.5, 0.3, 0.2])
        elif lat > 20:  # Central India
            veg_type = np.random.choice(['cropland', 'open_forest', 'scrubland', 'grassland'], p=[0.4, 0.2, 0.2, 0.2])
        elif lat > 15:  # Deccan
            veg_type = np.random.choice(['scrubland', 'cropland', 'barren', 'open_forest'], p=[0.3, 0.3, 0.2, 0.2])
        else:  # Southern
            veg_type = np.random.choice(['dense_forest', 'cropland', 'urban', 'grassland'], p=[0.3, 0.3, 0.2, 0.2])
        
        return veg_type, VEGETATION_MULTIPLIER.get(veg_type, 1.0)
    
    def _simulate_terrain(self, lat, lng):
        """Simulate terrain slope factor."""
        np.random.seed(int(abs(lat * 1000 + lng * 100 + 42)) % 2**31)
        
        # Slope in degrees
        if lat > 28:  # Mountains
            slope = np.random.uniform(10, 35)
        elif lat > 22:  # Hills
            slope = np.random.uniform(2, 15)
        else:  # Plains
            slope = np.random.uniform(0, 5)
        
        # Fire spreads ~2x faster uphill at 30 degrees
        slope_factor = 1.0 + (slope / 30.0) * 1.0
        return slope_factor
    
    def _compute_spread_ellipse(self, lat, lng, radius_km, wind_dir, wind_speed, t_hours):
        """Compute elliptical fire spread boundary."""
        # Ellipse elongation increases with wind speed
        eccentricity = min(0.8, wind_speed / 50.0)
        semi_major = radius_km * (1 + eccentricity)
        semi_minor = radius_km * (1 - eccentricity * 0.5)
        
        # Generate boundary points (for map overlay)
        n_points = 24
        angles = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
        
        boundary = []
        for angle in angles:
            # Elliptical radius at this angle
            r = (semi_major * semi_minor) / np.sqrt(
                (semi_minor * np.cos(angle)) ** 2 + (semi_major * np.sin(angle)) ** 2
            )
            
            # Rotate by wind direction
            rotated_angle = angle + np.radians(wind_dir)
            
            # Convert to lat/lng offsets (approximate)
            dlat = r * np.cos(rotated_angle) / 111.32  # 1 degree lat ≈ 111.32 km
            dlng = r * np.sin(rotated_angle) / (111.32 * np.cos(np.radians(lat)))
            
            boundary.append([round(lat + dlat, 5), round(lng + dlng, 5)])
        
        # Close the polygon
        boundary.append(boundary[0])
        
        return {
            'semi_major': semi_major,
            'semi_minor': semi_minor,
            'direction': wind_dir,
            'boundary_points': boundary,
        }
    
    def _classify_spread_risk(self, effective_rate):
        """Classify spread risk level."""
        if effective_rate > 8:
            return 'EXTREME'
        elif effective_rate > 5:
            return 'VERY_HIGH'
        elif effective_rate > 3:
            return 'HIGH'
        elif effective_rate > 1:
            return 'MODERATE'
        else:
            return 'LOW'


def predict_fire_spread(event_data):
    """Convenience function for single event prediction."""
    predictor = FireSpreadPredictor()
    return predictor.predict_spread(event_data)


if __name__ == "__main__":
    print("=== AGNI-DRISHTI: Fire Spread Predictor Test ===")
    
    test_event = {
        'target_class': 0,  # Wildfire
        'frp': 85.0,
        'lat': 24.5,
        'lng': 79.3,
    }
    
    result = predict_fire_spread(test_event)
    print(f"\nWind: {result['wind_speed_kmh']} km/h at {result['wind_direction_deg']}°")
    print(f"Vegetation: {result['vegetation_type']}")
    print(f"Effective Rate: {result['effective_spread_rate_kmh']} km/h")
    print(f"Spread Risk: {result['spread_risk']}")
    
    for horizon, pred in result['predictions'].items():
        print(f"\n{horizon}:")
        print(f"  Radius: {pred['radius_km']} km | Area: {pred['area_sq_km']} sq km | Confidence: {pred['confidence']}")
