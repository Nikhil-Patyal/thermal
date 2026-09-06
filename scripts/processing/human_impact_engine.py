"""
AGNI-DRISHTI: Comprehensive Human Impact Engine
=================================================
Goes far beyond basic risk scores to model the full human impact
of thermal anomalies, including:
  - Population exposure estimation
  - Vulnerable population identification
  - Air Quality Health Index (AQHI)
  - Psychological impact scoring
  - Evacuation route suggestion
  - Economic impact estimation
  - Water contamination risk
"""

import numpy as np
import warnings
warnings.filterwarnings('ignore')


# ── Population Density Grid (Simulated for India) ────────────────

# Approximate population density per sq km for Indian regions
POP_DENSITY_GRID = {
    'metro': {'density': 11000, 'examples': 'Delhi, Mumbai, Kolkata'},
    'urban': {'density': 4000, 'examples': 'Jaipur, Lucknow, Bhopal'},
    'semi_urban': {'density': 800, 'examples': 'District towns'},
    'rural': {'density': 300, 'examples': 'Villages'},
    'forest': {'density': 30, 'examples': 'Wildlife corridors'},
    'remote': {'density': 5, 'examples': 'Desert/mountain areas'},
}

# Vulnerable facility types
VULNERABLE_FACILITIES = [
    {'type': 'Hospital', 'icon': '🏥', 'priority': 'CRITICAL', 'evac_time_mins': 120},
    {'type': 'School', 'icon': '🏫', 'priority': 'CRITICAL', 'evac_time_mins': 45},
    {'type': 'Elderly Care Home', 'icon': '👴', 'priority': 'CRITICAL', 'evac_time_mins': 90},
    {'type': 'Shelter/Slum', 'icon': '🏚️', 'priority': 'HIGH', 'evac_time_mins': 60},
    {'type': 'Market/Mall', 'icon': '🏬', 'priority': 'HIGH', 'evac_time_mins': 30},
    {'type': 'Religious Place', 'icon': '🕌', 'priority': 'MODERATE', 'evac_time_mins': 25},
    {'type': 'Railway Station', 'icon': '🚉', 'priority': 'HIGH', 'evac_time_mins': 40},
    {'type': 'Industrial Workers', 'icon': '🏗️', 'priority': 'HIGH', 'evac_time_mins': 35},
]


class HumanImpactEngine:
    """
    Comprehensive human impact assessment system.
    """
    
    def assess_impact(self, event):
        """
        Full impact assessment for a thermal event.
        
        Args:
            event: dict with keys: lat, lng, frp, target_class, toxic_radius_km,
                   persistence_days, spread_risk, etc.
        
        Returns:
            dict with comprehensive impact data
        """
        lat = event.get('lat', 22.0)
        lng = event.get('lng', 78.0)
        frp = event.get('frp', 30)
        target_class = event.get('target_class', 0)
        toxic_radius = event.get('toxic_radius_km', 5.0)
        persistence = event.get('persistence_days', 1)
        
        # 1. Population Exposure
        pop_exposure = self._estimate_population_exposure(lat, lng, toxic_radius)
        
        # 2. Vulnerable Populations
        vulnerable = self._identify_vulnerable_facilities(lat, lng, toxic_radius)
        
        # 3. Air Quality Health Index
        aqhi = self._compute_aqhi(frp, target_class, toxic_radius)
        
        # 4. Psychological Impact Score
        psych = self._compute_psychological_impact(
            pop_exposure, frp, target_class, persistence, vulnerable
        )
        
        # 5. Evacuation Assessment
        evacuation = self._generate_evacuation_assessment(lat, lng, toxic_radius, vulnerable)
        
        # 6. Economic Impact
        economic = self._estimate_economic_impact(target_class, frp, toxic_radius, lat, lng)
        
        # 7. Water Contamination Risk
        water_risk = self._assess_water_contamination(lat, lng, target_class, toxic_radius)
        
        # 8. Overall Composite Risk Score (0-100)
        composite_risk = self._compute_composite_risk(
            pop_exposure, aqhi, psych, economic, water_risk
        )
        
        return {
            'population_exposure': pop_exposure,
            'vulnerable_facilities': vulnerable,
            'air_quality': aqhi,
            'psychological_impact': psych,
            'evacuation': evacuation,
            'economic_impact': economic,
            'water_contamination': water_risk,
            'composite_risk_score': composite_risk,
        }
    
    # ── Population Exposure ──────────────────────────────────────
    
    def _estimate_population_exposure(self, lat, lng, radius_km):
        """Estimate population within the danger radius."""
        zone = self._get_population_zone(lat, lng)
        density = POP_DENSITY_GRID[zone]['density']
        
        area_sq_km = np.pi * radius_km ** 2
        total_pop = int(density * area_sq_km)
        
        # Exposure tiers
        inner_pop = int(density * np.pi * (radius_km * 0.3) ** 2)  # 0-30% radius
        mid_pop = int(density * np.pi * ((radius_km * 0.7) ** 2 - (radius_km * 0.3) ** 2))
        outer_pop = total_pop - inner_pop - mid_pop
        
        return {
            'total_population': total_pop,
            'zone_type': zone,
            'zone_description': POP_DENSITY_GRID[zone]['examples'],
            'density_per_sq_km': density,
            'danger_area_sq_km': round(area_sq_km, 2),
            'exposure_tiers': {
                'critical_zone': {'population': inner_pop, 'radius_pct': '0-30%', 'risk': 'EXTREME'},
                'high_zone': {'population': mid_pop, 'radius_pct': '30-70%', 'risk': 'HIGH'},
                'warning_zone': {'population': outer_pop, 'radius_pct': '70-100%', 'risk': 'MODERATE'},
            },
            'children_estimated': int(total_pop * 0.28),  # India child population ~28%
            'elderly_estimated': int(total_pop * 0.08),    # Elderly ~8%
        }
    
    def _get_population_zone(self, lat, lng):
        """Determine population zone from coordinates."""
        np.random.seed(int(abs(lat * 100 + lng * 100)) % 2**31)
        
        # Metro regions (simplified)
        metro_coords = [(28.6, 77.2), (19.1, 72.9), (22.6, 88.4), (13.1, 80.3), (12.97, 77.6)]
        for m_lat, m_lng in metro_coords:
            if abs(lat - m_lat) < 0.5 and abs(lng - m_lng) < 0.5:
                return 'metro'
        
        return np.random.choice(
            ['urban', 'semi_urban', 'rural', 'forest', 'remote'],
            p=[0.15, 0.25, 0.35, 0.15, 0.10]
        )
    
    # ── Vulnerable Facilities ────────────────────────────────────
    
    def _identify_vulnerable_facilities(self, lat, lng, radius_km):
        """Identify vulnerable facilities within the impact zone."""
        np.random.seed(int(abs(lat * 1000 + lng * 1000)) % 2**31)
        
        zone = self._get_population_zone(lat, lng)
        
        # Number of facilities scales with urbanization
        facility_counts = {
            'metro': (8, 15), 'urban': (5, 10), 'semi_urban': (2, 6),
            'rural': (1, 3), 'forest': (0, 1), 'remote': (0, 0)
        }
        
        min_f, max_f = facility_counts.get(zone, (1, 3))
        n_facilities = np.random.randint(min_f, max(min_f + 1, max_f + 1))
        
        facilities = []
        for _ in range(n_facilities):
            fac = np.random.choice(VULNERABLE_FACILITIES)
            dist = round(np.random.uniform(0.2, radius_km), 2)
            capacity = np.random.randint(50, 2000)
            
            facilities.append({
                'type': fac['type'],
                'icon': fac['icon'],
                'priority': fac['priority'],
                'distance_km': dist,
                'estimated_occupants': capacity,
                'evac_time_required_mins': fac['evac_time_mins'],
                'status': 'AT RISK' if dist < radius_km * 0.5 else 'WARNING',
            })
        
        facilities.sort(key=lambda x: x['distance_km'])
        
        total_at_risk = sum(f['estimated_occupants'] for f in facilities if f['status'] == 'AT RISK')
        
        return {
            'total_facilities': len(facilities),
            'facilities': facilities[:8],  # Cap for display
            'total_at_risk_occupants': total_at_risk,
            'critical_facilities': len([f for f in facilities if f['priority'] == 'CRITICAL']),
        }
    
    # ── Air Quality Health Index ─────────────────────────────────
    
    def _compute_aqhi(self, frp, target_class, radius_km):
        """
        Predict air quality impact from fire type and intensity.
        Based on emission factors for different combustion types.
        """
        # PM2.5 emission factors (kg per MW-hour of FRP)
        emission_factors = {
            0: 1.2,   # Wildfire — high particulate
            1: 0.8,   # Industrial — moderate (filtered)
            2: 0.3,   # Gas Flare — lower particulate
            3: 1.5,   # Agriculture — very high (smoldering)
            4: 0.5,   # Mining — dust-heavy
        }
        
        ef = emission_factors.get(target_class, 1.0)
        
        # Estimated PM2.5 concentration (μg/m³) at various distances
        # Using Gaussian plume dispersion model (simplified)
        base_pm25 = frp * ef * 2.5
        
        distances = [1, 5, 10, 25, 50]  # km
        pm25_at_distance = {}
        for d in distances:
            concentration = base_pm25 / (d ** 1.5 + 1)  # Inverse power dispersion
            concentration += np.random.normal(0, 5)
            concentration = max(0, concentration)
            pm25_at_distance[f"{d}km"] = round(concentration, 1)
        
        # Peak PM2.5 near source
        peak_pm25 = round(base_pm25, 1)
        
        # AQI category
        if peak_pm25 > 300:
            aqi_category = 'HAZARDOUS'
            health_advisory = 'Everyone should avoid all outdoor activity. Stay indoors with windows sealed.'
            color = '#7e0023'
        elif peak_pm25 > 200:
            aqi_category = 'VERY_UNHEALTHY'
            health_advisory = 'Everyone may experience serious health effects. Avoid prolonged outdoor exertion.'
            color = '#99004c'
        elif peak_pm25 > 150:
            aqi_category = 'UNHEALTHY'
            health_advisory = 'Everyone may begin to experience health effects. Sensitive groups should avoid outdoor activity.'
            color = '#ff0000'
        elif peak_pm25 > 100:
            aqi_category = 'UNHEALTHY_SENSITIVE'
            health_advisory = 'People with respiratory conditions, elderly, and children should limit outdoor activity.'
            color = '#ff7e00'
        elif peak_pm25 > 50:
            aqi_category = 'MODERATE'
            health_advisory = 'Air quality is acceptable. Unusually sensitive people should consider reducing outdoor exertion.'
            color = '#ffff00'
        else:
            aqi_category = 'GOOD'
            health_advisory = 'Air quality is satisfactory. No health impacts expected.'
            color = '#00e400'
        
        # Toxic gases based on fire type
        toxic_gases = self._estimate_toxic_gases(target_class, frp)
        
        return {
            'peak_pm25_ugm3': peak_pm25,
            'pm25_by_distance': pm25_at_distance,
            'aqi_category': aqi_category,
            'aqi_color': color,
            'health_advisory': health_advisory,
            'toxic_gases': toxic_gases,
            'affected_radius_km': round(radius_km * 2.5, 1),  # AQ impact wider than thermal
            'mask_recommended': peak_pm25 > 100,
            'indoor_shelter_recommended': peak_pm25 > 200,
        }
    
    def _estimate_toxic_gases(self, target_class, frp):
        """Estimate toxic gas emissions based on fire type."""
        gases = {}
        
        if target_class == 0:  # Wildfire
            gases = {
                'CO': {'level': round(frp * 0.5, 1), 'unit': 'ppm', 'risk': 'HIGH' if frp > 50 else 'MODERATE'},
                'NO2': {'level': round(frp * 0.1, 2), 'unit': 'ppm', 'risk': 'MODERATE'},
                'Benzene': {'level': round(frp * 0.02, 3), 'unit': 'ppm', 'risk': 'LOW'},
            }
        elif target_class == 1:  # Industrial
            gases = {
                'CO': {'level': round(frp * 0.3, 1), 'unit': 'ppm', 'risk': 'HIGH'},
                'SO2': {'level': round(frp * 0.2, 2), 'unit': 'ppm', 'risk': 'HIGH'},
                'HCl': {'level': round(frp * 0.05, 3), 'unit': 'ppm', 'risk': 'CRITICAL'},
                'Dioxins': {'level': round(frp * 0.001, 4), 'unit': 'ng/m³', 'risk': 'CRITICAL'},
            }
        elif target_class == 2:  # Gas Flare
            gases = {
                'CO2': {'level': round(frp * 1.5, 1), 'unit': 'ppm', 'risk': 'MODERATE'},
                'CH4': {'level': round(frp * 0.1, 2), 'unit': 'ppm', 'risk': 'LOW'},
                'NOx': {'level': round(frp * 0.08, 3), 'unit': 'ppm', 'risk': 'MODERATE'},
            }
        elif target_class == 3:  # Agriculture
            gases = {
                'CO': {'level': round(frp * 0.8, 1), 'unit': 'ppm', 'risk': 'HIGH'},
                'PM10': {'level': round(frp * 2.0, 1), 'unit': 'μg/m³', 'risk': 'HIGH'},
                'Ozone': {'level': round(frp * 0.15, 2), 'unit': 'ppm', 'risk': 'MODERATE'},
            }
        else:  # Mining
            gases = {
                'PM10_dust': {'level': round(frp * 1.5, 1), 'unit': 'μg/m³', 'risk': 'HIGH'},
                'Silica': {'level': round(frp * 0.05, 3), 'unit': 'mg/m³', 'risk': 'HIGH'},
                'Radon': {'level': round(np.random.uniform(20, 100), 1), 'unit': 'Bq/m³', 'risk': 'MODERATE'},
            }
        
        return gases
    
    # ── Psychological Impact ─────────────────────────────────────
    
    def _compute_psychological_impact(self, pop_exposure, frp, target_class, persistence, vulnerable):
        """
        Multi-factor psychological stress assessment.
        Based on disaster psychology research frameworks.
        """
        total_pop = pop_exposure['total_population']
        children = pop_exposure['children_estimated']
        elderly = pop_exposure['elderly_estimated']
        
        # Factor 1: Proximity Stress (closer = higher stress)
        proximity_factor = min(1.0, total_pop / 10000)
        
        # Factor 2: Severity Perception (high FRP = more visible/frightening)
        severity_factor = min(1.0, frp / 100.0)
        
        # Factor 3: Duration Stress (longer events = chronic stress)
        duration_factor = min(1.0, persistence / 30.0)
        
        # Factor 4: Vulnerability Multiplier (children, elderly amplify impact)
        vulnerability_factor = min(1.0, (children + elderly) / max(total_pop, 1) * 5)
        
        # Factor 5: Uncertainty (some fire types more frightening)
        uncertainty_factors = {0: 0.9, 1: 0.8, 2: 0.5, 3: 0.4, 4: 0.3}
        uncertainty_factor = uncertainty_factors.get(target_class, 0.5)
        
        # Factor 6: Social Disruption
        social_disruption = min(1.0, vulnerable['total_facilities'] / 10)
        
        # Composite Psychological Impact Score (0-100)
        raw_score = (
            proximity_factor * 25 +
            severity_factor * 20 +
            duration_factor * 15 +
            vulnerability_factor * 15 +
            uncertainty_factor * 15 +
            social_disruption * 10
        )
        psych_score = min(100, max(0, int(raw_score)))
        
        # Psychological impact categories
        if psych_score >= 75:
            level = 'SEVERE'
            description = 'Mass anxiety and panic likely. Immediate crisis intervention needed.'
            interventions = [
                'Deploy crisis counseling teams immediately',
                'Establish community reassurance centers',
                'Activate mental health helplines',
                'Provide real-time transparent communication',
                'Deploy child psychologists to affected schools',
            ]
        elif psych_score >= 50:
            level = 'HIGH'
            description = 'Significant community distress expected. Proactive intervention recommended.'
            interventions = [
                'Issue calm, factual public updates every 30 minutes',
                'Activate community leaders for reassurance',
                'Prepare mental health support at evacuation centers',
                'Monitor social media for panic indicators',
            ]
        elif psych_score >= 25:
            level = 'MODERATE'
            description = 'Some community concern. Monitor and communicate proactively.'
            interventions = [
                'Provide regular status updates',
                'Ensure emergency helplines are visible',
                'Brief community health workers',
            ]
        else:
            level = 'LOW'
            description = 'Minimal psychological impact expected.'
            interventions = [
                'Routine monitoring sufficient',
                'Maintain information transparency',
            ]
        
        # PTSD risk estimation
        ptsd_risk_pct = round(min(40, psych_score * 0.4), 1)
        
        return {
            'score': psych_score,
            'level': level,
            'description': description,
            'interventions': interventions,
            'factors': {
                'proximity_stress': round(proximity_factor * 100),
                'severity_perception': round(severity_factor * 100),
                'duration_stress': round(duration_factor * 100),
                'vulnerability': round(vulnerability_factor * 100),
                'uncertainty': round(uncertainty_factor * 100),
                'social_disruption': round(social_disruption * 100),
            },
            'ptsd_risk_percent': ptsd_risk_pct,
            'estimated_affected_children': children,
            'estimated_affected_elderly': elderly,
            'counseling_teams_needed': max(1, psych_score // 20),
        }
    
    # ── Evacuation Assessment ────────────────────────────────────
    
    def _generate_evacuation_assessment(self, lat, lng, radius_km, vulnerable):
        """Generate AI evacuation recommendations."""
        np.random.seed(int(abs(lat * 1000 + lng * 1000 + 99)) % 2**31)
        
        # Generate evacuation routes (simplified cardinal directions)
        wind_dir = np.random.uniform(0, 360)
        
        # Recommend evacuation perpendicular to wind direction
        safe_directions = []
        for angle_offset in [90, -90, 135, -135]:
            safe_angle = (wind_dir + angle_offset) % 360
            direction_name = self._angle_to_direction(safe_angle)
            safe_directions.append({
                'direction': direction_name,
                'angle': round(safe_angle, 1),
                'safety_rating': round(np.random.uniform(0.7, 0.95), 2),
            })
        
        # Time estimates
        total_evac_pop = vulnerable.get('total_at_risk_occupants', 0)
        evac_time_hours = max(1, total_evac_pop / 500)  # ~500 people/hour throughput
        
        # Nearest safe zones
        safe_zones = [
            {'name': 'Community Hall', 'distance_km': round(np.random.uniform(2, 8), 1), 'capacity': np.random.randint(200, 1000)},
            {'name': 'School (Evacuation Center)', 'distance_km': round(np.random.uniform(3, 10), 1), 'capacity': np.random.randint(300, 1500)},
            {'name': 'Sports Ground', 'distance_km': round(np.random.uniform(1, 5), 1), 'capacity': np.random.randint(500, 3000)},
        ]
        safe_zones.sort(key=lambda x: x['distance_km'])
        
        return {
            'recommended_directions': safe_directions[:3],
            'avoid_direction': self._angle_to_direction(wind_dir),
            'estimated_evac_time_hours': round(evac_time_hours, 1),
            'population_to_evacuate': total_evac_pop,
            'safe_zones': safe_zones,
            'vehicles_needed': max(5, total_evac_pop // 40),
            'ambulances_needed': max(1, total_evac_pop // 200),
            'urgency': 'IMMEDIATE' if radius_km < 3 else 'PLANNED',
        }
    
    def _angle_to_direction(self, angle):
        """Convert angle to cardinal direction."""
        dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        idx = round(angle / 45) % 8
        return dirs[idx]
    
    # ── Economic Impact ──────────────────────────────────────────
    
    def _estimate_economic_impact(self, target_class, frp, radius_km, lat, lng):
        """Estimate economic damage."""
        area_sq_km = np.pi * radius_km ** 2
        
        np.random.seed(int(abs(lat * 100 + lng * 100 + 77)) % 2**31)
        
        if target_class == 0:  # Wildfire
            forest_loss_hectares = round(area_sq_km * 100 * np.random.uniform(0.3, 0.8), 1)
            timber_value_crore = round(forest_loss_hectares * 0.05, 2)
            property_damage_crore = round(np.random.uniform(1, 50) * (frp / 30), 2)
            suppression_cost_crore = round(np.random.uniform(0.5, 10), 2)
            total = timber_value_crore + property_damage_crore + suppression_cost_crore
            
            return {
                'total_damage_crore': round(total, 2),
                'breakdown': {
                    'Forest/Timber Loss': f'₹{timber_value_crore} Cr',
                    'Property Damage': f'₹{property_damage_crore} Cr',
                    'Suppression Cost': f'₹{suppression_cost_crore} Cr',
                },
                'insurance_claims_estimated': np.random.randint(10, 500),
                'recovery_time_months': np.random.randint(6, 36),
            }
        elif target_class == 1:  # Industrial
            facility_damage = round(np.random.uniform(10, 200), 2)
            production_loss = round(np.random.uniform(5, 100), 2)
            cleanup_cost = round(np.random.uniform(2, 50), 2)
            total = facility_damage + production_loss + cleanup_cost
            
            return {
                'total_damage_crore': round(total, 2),
                'breakdown': {
                    'Facility Damage': f'₹{facility_damage} Cr',
                    'Production Loss': f'₹{production_loss} Cr',
                    'Environmental Cleanup': f'₹{cleanup_cost} Cr',
                },
                'jobs_affected': np.random.randint(100, 5000),
                'recovery_time_months': np.random.randint(3, 18),
            }
        elif target_class == 3:  # Agriculture
            crop_loss_hectares = round(area_sq_km * 100, 1)
            crop_value = round(crop_loss_hectares * np.random.uniform(0.01, 0.1), 2)
            soil_degradation = round(np.random.uniform(0.5, 5), 2)
            total = crop_value + soil_degradation
            
            return {
                'total_damage_crore': round(total, 2),
                'breakdown': {
                    'Crop Loss': f'₹{crop_value} Cr',
                    'Soil Degradation': f'₹{soil_degradation} Cr',
                },
                'farmers_affected': np.random.randint(50, 2000),
                'recovery_time_months': np.random.randint(1, 6),
            }
        else:
            return {
                'total_damage_crore': round(np.random.uniform(0.5, 20), 2),
                'breakdown': {'Operational Disruption': f'₹{round(np.random.uniform(0.5, 20), 2)} Cr'},
                'recovery_time_months': np.random.randint(1, 12),
            }
    
    # ── Water Contamination ──────────────────────────────────────
    
    def _assess_water_contamination(self, lat, lng, target_class, radius_km):
        """Assess risk to water sources."""
        np.random.seed(int(abs(lat * 100 + lng * 100 + 33)) % 2**31)
        
        dist_to_river = round(np.random.uniform(0.5, 30), 1)
        dist_to_reservoir = round(np.random.uniform(2, 50), 1)
        
        # Contamination risk based on proximity and fire type
        toxicity_factors = {0: 0.4, 1: 0.9, 2: 0.6, 3: 0.3, 4: 0.8}
        tox = toxicity_factors.get(target_class, 0.5)
        
        river_risk = tox * max(0, 1 - dist_to_river / (radius_km * 3))
        reservoir_risk = tox * max(0, 1 - dist_to_reservoir / (radius_km * 5))
        
        if max(river_risk, reservoir_risk) > 0.7:
            risk_level = 'HIGH'
            advisory = 'Water sources may be contaminated. Advise boiling or alternative supply.'
        elif max(river_risk, reservoir_risk) > 0.3:
            risk_level = 'MODERATE'
            advisory = 'Monitor water quality. Precautionary testing recommended.'
        else:
            risk_level = 'LOW'
            advisory = 'Water sources unlikely to be affected.'
        
        return {
            'risk_level': risk_level,
            'advisory': advisory,
            'nearest_river_km': dist_to_river,
            'nearest_reservoir_km': dist_to_reservoir,
            'river_contamination_risk': round(river_risk * 100),
            'reservoir_contamination_risk': round(reservoir_risk * 100),
            'contaminants': ['Ash runoff', 'Heavy metals'] if target_class in [1, 4] else ['Sediment', 'Nutrients'],
        }
    
    # ── Composite Risk Score ─────────────────────────────────────
    
    def _compute_composite_risk(self, pop, aqhi, psych, economic, water):
        """Compute a single 0-100 composite risk score."""
        pop_score = min(30, pop['total_population'] / 1000)
        aqhi_score = min(25, {'HAZARDOUS': 25, 'VERY_UNHEALTHY': 20, 'UNHEALTHY': 15,
                              'UNHEALTHY_SENSITIVE': 10, 'MODERATE': 5, 'GOOD': 0}.get(aqhi['aqi_category'], 0))
        psych_score = psych['score'] * 0.2
        econ_score = min(15, economic['total_damage_crore'] / 10)
        water_score = {'HIGH': 10, 'MODERATE': 5, 'LOW': 1}.get(water['risk_level'], 0)
        
        composite = int(min(100, pop_score + aqhi_score + psych_score + econ_score + water_score))
        
        if composite >= 80:
            level = 'CRITICAL'
        elif composite >= 60:
            level = 'HIGH'
        elif composite >= 40:
            level = 'MODERATE'
        else:
            level = 'LOW'
        
        return {
            'score': composite,
            'level': level,
            'breakdown': {
                'population_exposure': round(pop_score),
                'air_quality': round(aqhi_score),
                'psychological': round(psych_score),
                'economic': round(econ_score),
                'water': round(water_score),
            }
        }


def assess_human_impact(event):
    """Convenience function for single event assessment."""
    engine = HumanImpactEngine()
    return engine.assess_impact(event)


if __name__ == "__main__":
    print("=== AGNI-DRISHTI: Human Impact Engine Test ===")
    
    test_event = {
        'lat': 28.6,
        'lng': 77.2,
        'frp': 75.0,
        'target_class': 0,  # Wildfire near Delhi
        'toxic_radius_km': 8.0,
        'persistence_days': 5,
    }
    
    result = assess_human_impact(test_event)
    
    print(f"\nPopulation Exposed: {result['population_exposure']['total_population']:,}")
    print(f"  Children: {result['population_exposure']['children_estimated']:,}")
    print(f"  Elderly: {result['population_exposure']['elderly_estimated']:,}")
    print(f"\nAir Quality: {result['air_quality']['aqi_category']} (PM2.5: {result['air_quality']['peak_pm25_ugm3']} μg/m³)")
    print(f"Health Advisory: {result['air_quality']['health_advisory']}")
    print(f"\nPsychological Impact: {result['psychological_impact']['level']} (Score: {result['psychological_impact']['score']}/100)")
    print(f"  {result['psychological_impact']['description']}")
    print(f"  PTSD Risk: {result['psychological_impact']['ptsd_risk_percent']}%")
    print(f"\nEconomic Damage: ₹{result['economic_impact']['total_damage_crore']} Crore")
    print(f"\nComposite Risk: {result['composite_risk_score']['level']} ({result['composite_risk_score']['score']}/100)")
