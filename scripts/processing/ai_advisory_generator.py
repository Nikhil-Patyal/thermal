"""
AGNI-DRISHTI: AI Advisory Generator
=====================================
Generates human-readable intelligence reports and advisory text
for each thermal event:
  - Situation summary in natural language
  - Action recommendations for NDRF/SDRF/local authorities
  - Public advisory (Hindi + English)
  - Psychological first-aid guidance
  - Social media alert templates
"""

import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


CLASS_NAMES = ['Wildfire', 'Industrial Fire', 'Gas Flare', 'Agriculture Burning', 'Mining Activity']
CLASS_DESCRIPTIONS = {
    0: 'vegetation/forest fire involving organic biomass combustion',
    1: 'industrial facility fire involving chemical/structural combustion',
    2: 'persistent gas flare from petroleum/natural gas operations',
    3: 'agricultural crop residue burning (stubble/slash burning)',
    4: 'mining operation thermal emission from extraction/processing activities',
}


class AIAdvisoryGenerator:
    """
    NLP-style advisory generator for thermal events.
    Produces comprehensive intelligence briefs.
    """
    
    def generate_advisory(self, event, impact_data, method_scores, spread_data=None):
        """
        Generate complete AI advisory for an event.
        
        Args:
            event: Event data dict (lat, lng, type, confidence, frp, etc.)
            impact_data: Output from HumanImpactEngine
            method_scores: Dict of method→confidence scores
            spread_data: Optional spread prediction data
        """
        target_class = event.get('target_class', 0)
        
        advisory = {
            'situation_report': self._generate_sitrep(event, impact_data, method_scores),
            'action_items': self._generate_action_items(event, impact_data, target_class),
            'public_advisory_en': self._generate_public_advisory_en(event, impact_data, target_class),
            'public_advisory_hi': self._generate_public_advisory_hi(event, impact_data, target_class),
            'psychological_guidance': self._generate_psych_guidance(impact_data, target_class),
            'social_media_alert': self._generate_social_media(event, impact_data),
            'sms_alert': self._generate_sms_alert(event, impact_data),
            'authority_brief': self._generate_authority_brief(event, impact_data, spread_data),
            'ai_recommendation': self._generate_ai_recommendation(event, impact_data, spread_data),
        }
        
        return advisory
    
    # ── Situation Report ─────────────────────────────────────────
    
    def _generate_sitrep(self, event, impact, method_scores):
        """Generate structured situation report."""
        conf = event.get('confidence', 0)
        frp = event.get('frp', 0)
        lat = event.get('lat', 0)
        lng = event.get('lng', 0)
        event_type = event.get('type', 'Unknown')
        risk = impact.get('composite_risk_score', {}).get('level', 'UNKNOWN')
        pop = impact.get('population_exposure', {}).get('total_population', 0)
        aqhi = impact.get('air_quality', {}).get('aqi_category', 'UNKNOWN')
        
        # Method consensus
        if method_scores:
            agreeing = sum(1 for v in method_scores.values() if v > 50)
            total = len(method_scores)
            consensus = f"{agreeing}/{total} AI methods agree on classification"
        else:
            consensus = "Classification pending"
        
        timestamp = datetime.now().strftime("%d %b %Y %H:%M IST")
        
        report = (
            f"AGNI-DRISHTI SITUATION REPORT — {timestamp}\n"
            f"{'='*55}\n\n"
            f"EVENT TYPE: {event_type.upper()} (Confidence: {conf}%)\n"
            f"LOCATION: {lat}°N, {lng}°E\n"
            f"FIRE RADIATIVE POWER: {frp} MW\n"
            f"RISK LEVEL: {risk}\n\n"
            f"AI CONSENSUS: {consensus}\n\n"
            f"SITUATION SUMMARY:\n"
            f"A {CLASS_DESCRIPTIONS.get(event.get('target_class', 0), 'thermal anomaly')} has been "
            f"detected at coordinates {lat}°N, {lng}°E with Fire Radiative Power of {frp} MW. "
            f"The multi-method AI ensemble has classified this event as '{event_type}' with "
            f"{conf}% confidence.\n\n"
            f"HUMAN IMPACT:\n"
            f"• Estimated population in danger zone: {pop:,}\n"
            f"• Air quality impact: {aqhi}\n"
            f"• Psychological impact level: {impact.get('psychological_impact', {}).get('level', 'N/A')}\n"
            f"• Economic damage estimate: ₹{impact.get('economic_impact', {}).get('total_damage_crore', 0)} Crore\n"
        )
        
        return report
    
    # ── Action Items ─────────────────────────────────────────────
    
    def _generate_action_items(self, event, impact, target_class):
        """Generate prioritized action items for authorities."""
        risk_level = impact.get('composite_risk_score', {}).get('level', 'LOW')
        pop = impact.get('population_exposure', {}).get('total_population', 0)
        
        actions = []
        
        if target_class == 0:  # Wildfire
            actions = [
                {'priority': 'P0', 'action': 'Deploy aerial firefighting units (Mi-17/Mi-26) to containment perimeter', 'responsible': 'NDRF/IAF'},
                {'priority': 'P0', 'action': 'Establish firebreaks along predicted spread path', 'responsible': 'Forest Department'},
                {'priority': 'P1', 'action': 'Evacuate settlements within predicted T+3h fire boundary', 'responsible': 'District Administration'},
                {'priority': 'P1', 'action': 'Activate community alert sirens and PA systems', 'responsible': 'Local Administration'},
                {'priority': 'P2', 'action': 'Deploy air quality monitoring stations downwind', 'responsible': 'CPCB/SPCB'},
                {'priority': 'P2', 'action': 'Set up medical camps with respiratory care', 'responsible': 'Health Department'},
                {'priority': 'P3', 'action': 'Coordinate with wildlife rescue teams for habitat areas', 'responsible': 'Forest Department'},
            ]
        elif target_class == 1:  # Industrial
            actions = [
                {'priority': 'P0', 'action': 'Dispatch industrial fire response team with HAZMAT equipment', 'responsible': 'NDRF HAZMAT Unit'},
                {'priority': 'P0', 'action': 'Establish 2km exclusion zone around facility', 'responsible': 'Police/SDRF'},
                {'priority': 'P1', 'action': 'Identify chemicals stored at facility for toxicity assessment', 'responsible': 'Factory Inspectorate'},
                {'priority': 'P1', 'action': 'Issue immediate shelter-in-place advisory downwind', 'responsible': 'District Magistrate'},
                {'priority': 'P2', 'action': 'Monitor groundwater contamination', 'responsible': 'Pollution Control Board'},
            ]
        elif target_class == 3:  # Agriculture
            actions = [
                {'priority': 'P1', 'action': 'Issue air quality advisory for surrounding villages', 'responsible': 'Health Department'},
                {'priority': 'P2', 'action': 'Document burning for enforcement under NGT orders', 'responsible': 'Revenue Department'},
                {'priority': 'P2', 'action': 'Deploy happy seeder/bio-decomposer awareness teams', 'responsible': 'Agriculture Department'},
                {'priority': 'P3', 'action': 'Monitor crop loss for insurance claims', 'responsible': 'Agriculture Department'},
            ]
        else:
            actions = [
                {'priority': 'P1', 'action': 'Verify source and confirm classification', 'responsible': 'Monitoring Cell'},
                {'priority': 'P2', 'action': 'Document for compliance database', 'responsible': 'Environment Department'},
            ]
        
        # Add universal actions for high-risk events
        if risk_level in ['CRITICAL', 'HIGH']:
            actions.insert(0, {'priority': 'P0', 'action': f'ALERT: Activate Emergency Operations Center. {pop:,} people potentially affected.', 'responsible': 'District Collector'})
        
        if impact.get('psychological_impact', {}).get('level') in ['SEVERE', 'HIGH']:
            actions.append({'priority': 'P1', 'action': 'Deploy crisis counseling and psychological first-aid teams', 'responsible': 'Mental Health Dept / NGOs'})
        
        return actions
    
    # ── Public Advisory (English) ────────────────────────────────
    
    def _generate_public_advisory_en(self, event, impact, target_class):
        """Generate public-facing advisory in English."""
        event_type = event.get('type', 'thermal anomaly')
        aqhi = impact.get('air_quality', {})
        evacuation = impact.get('evacuation', {})
        
        advisory = (
            f"⚠️ AGNI-DRISHTI PUBLIC SAFETY ADVISORY ⚠️\n\n"
            f"A {event_type.lower()} has been detected in your area.\n\n"
            f"AIR QUALITY: {aqhi.get('aqi_category', 'UNKNOWN')}\n"
            f"📋 {aqhi.get('health_advisory', '')}\n\n"
            f"SAFETY INSTRUCTIONS:\n"
        )
        
        if target_class == 0:  # Wildfire
            advisory += (
                "• If you see or smell smoke, move indoors immediately\n"
                "• Close all windows and doors, seal gaps with wet cloth\n"
                "• Keep emergency supplies ready (water, medicines, documents)\n"
                "• If evacuation is ordered, move in the direction AWAY from smoke\n"
                "• Do NOT return to affected areas until officially cleared\n"
                "• Check on elderly neighbors and people with respiratory conditions\n"
            )
        elif target_class == 1:
            advisory += (
                "• SHELTER IN PLACE unless evacuation is specifically ordered\n"
                "• Do NOT approach the facility or plume\n"
                "• Close all windows, turn off AC and ventilation systems\n"
                "• Cover nose and mouth with a damp cloth if outdoors\n"
                "• If you experience breathing difficulty, call 108 immediately\n"
            )
        elif target_class == 3:
            advisory += (
                "• Avoid outdoor activities, especially morning exercise\n"
                "• Use N95 masks if you must go outdoors\n"
                "• Keep children indoors during peak smoke hours\n"
                "• Use air purifiers if available\n"
                "• Drink plenty of water and eat jaggery/citrus fruits\n"
            )
        else:
            advisory += (
                "• Stay informed through official channels\n"
                "• Follow instructions from local authorities\n"
            )
        
        advisory += (
            f"\n📞 Emergency: 112 | Disaster: 1070 | NDRF: 011-24363260\n"
            f"🔗 Stay updated: agnidrishti.gov.in\n"
        )
        
        return advisory
    
    # ── Public Advisory (Hindi) ──────────────────────────────────
    
    def _generate_public_advisory_hi(self, event, impact, target_class):
        """Generate public-facing advisory in Hindi."""
        type_names_hi = {
            0: 'जंगल की आग', 1: 'औद्योगिक आग', 2: 'गैस फ्लेयर',
            3: 'पराली/कृषि दहन', 4: 'खनन गतिविधि'
        }
        event_type_hi = type_names_hi.get(target_class, 'तापीय विसंगति')
        
        advisory = (
            f"⚠️ अग्नि-दृष्टि जन सुरक्षा सूचना ⚠️\n\n"
            f"आपके क्षेत्र में {event_type_hi} का पता चला है।\n\n"
            f"सुरक्षा निर्देश:\n"
        )
        
        if target_class == 0:
            advisory += (
                "• यदि धुआं दिखे या गंध आए, तुरंत घर के अंदर जाएं\n"
                "• सभी खिड़कियां और दरवाज़े बंद करें, गीले कपड़े से अंतर भरें\n"
                "• आपातकालीन सामग्री तैयार रखें (पानी, दवाइयां, दस्तावेज़)\n"
                "• बुज़ुर्ग पड़ोसियों और सांस की बीमारी वालों की जांच करें\n"
                "• बिना अधिकारिक अनुमति के प्रभावित क्षेत्र में न लौटें\n"
            )
        elif target_class == 3:
            advisory += (
                "• बाहरी गतिविधियों से बचें, विशेषकर सुबह की सैर\n"
                "• बाहर जाने पर N95 मास्क का उपयोग करें\n"
                "• बच्चों को धुएं के समय घर के अंदर रखें\n"
                "• अधिक पानी पिएं और गुड़/नींबू खाएं\n"
            )
        else:
            advisory += (
                "• आधिकारिक चैनलों से जानकारी लेते रहें\n"
                "• स्थानीय अधिकारियों के निर्देशों का पालन करें\n"
            )
        
        advisory += (
            f"\n📞 आपातकालीन: 112 | आपदा: 1070\n"
        )
        
        return advisory
    
    # ── Psychological First-Aid Guidance ─────────────────────────
    
    def _generate_psych_guidance(self, impact, target_class):
        """Generate psychological first-aid guidance."""
        psych = impact.get('psychological_impact', {})
        level = psych.get('level', 'LOW')
        
        guidance = {
            'for_responders': [
                'Approach affected people calmly and with empathy',
                'Provide clear, simple information about what is happening',
                'Help people connect with family members',
                'Identify people showing signs of acute distress (trembling, disorientation)',
                'Do NOT force people to talk about what they saw',
                'Ensure basic needs are met (water, shade, seating)',
            ],
            'for_families': [
                'Talk to children honestly but calmly about what happened',
                'Maintain normal routines as much as possible',
                'Limit exposure to news coverage and social media',
                'Physical activity helps — walk, stretch, deep breathe',
                'It is normal to feel anxious — these feelings will reduce over time',
                'Seek professional help if anxiety persists beyond 2 weeks',
            ],
            'for_children': [
                'Reassure children that they are safe',
                'Let them express feelings through drawing or play',
                'Keep them close to a trusted adult',
                'Answer questions simply and honestly',
                'Watch for behavior changes (bedwetting, clinginess, nightmares)',
            ],
            'helplines': [
                {'name': 'NIMHANS Helpline', 'number': '080-46110007'},
                {'name': 'Vandrevala Foundation', 'number': '1860-2662-345'},
                {'name': 'iCall', 'number': '9152987821'},
                {'name': 'KIRAN Mental Health', 'number': '1800-599-0019'},
            ],
        }
        
        if level in ['SEVERE', 'HIGH']:
            guidance['urgent_measures'] = [
                'DEPLOY crisis intervention teams within 2 hours',
                'Establish psychological first-aid stations at every evacuation point',
                'Arrange community grief counseling sessions within 48 hours',
                'Monitor social media for suicide risk indicators',
                'Provide 24/7 helpline access with trained counselors',
            ]
        
        return guidance
    
    # ── Social Media Alert ───────────────────────────────────────
    
    def _generate_social_media(self, event, impact):
        """Generate social media alert template."""
        event_type = event.get('type', 'Thermal Anomaly')
        risk = impact.get('composite_risk_score', {}).get('level', 'UNKNOWN')
        pop = impact.get('population_exposure', {}).get('total_population', 0)
        
        tweet = (
            f"🔥 #AgniDrishti ALERT: {event_type} detected\n"
            f"📍 Location: {event.get('lat', 0):.2f}°N, {event.get('lng', 0):.2f}°E\n"
            f"⚠️ Risk: {risk} | 👥 {pop:,} people in zone\n"
            f"🛰️ AI Confidence: {event.get('confidence', 0)}%\n"
            f"Stay safe, follow local advisories.\n"
            f"#DisasterAlert #FireSafety #NDRF"
        )
        
        return {
            'twitter_template': tweet,
            'whatsapp_template': f"⚠️ *AGNI-DRISHTI Alert*\n{event_type} detected near your area.\nRisk Level: {risk}\nFollow safety instructions from authorities.\nEmergency: 112",
        }
    
    # ── SMS Alert ────────────────────────────────────────────────
    
    def _generate_sms_alert(self, event, impact):
        """Generate SMS alert text (within 160 char limit)."""
        event_type = event.get('type', 'Fire')
        risk = impact.get('composite_risk_score', {}).get('level', '')
        
        sms = f"AGNI-DRISHTI: {event_type} detected. Risk:{risk}. Stay indoors, seal windows. Follow local alerts. Emergency:112"
        return sms[:160]
    
    # ── Authority Brief ──────────────────────────────────────────
    
    def _generate_authority_brief(self, event, impact, spread_data):
        """Generate brief for district/state authorities."""
        pop = impact.get('population_exposure', {})
        evac = impact.get('evacuation', {})
        econ = impact.get('economic_impact', {})
        
        brief = (
            f"CLASSIFIED: FOR OFFICIAL USE ONLY\n"
            f"{'='*40}\n"
            f"AGNI-DRISHTI Intelligence Brief\n\n"
            f"THREAT: {event.get('type', 'Unknown')}\n"
            f"CONFIDENCE: {event.get('confidence', 0)}% (Multi-AI Ensemble)\n"
            f"POPULATION AT RISK: {pop.get('total_population', 0):,}\n"
            f"  - Children: {pop.get('children_estimated', 0):,}\n"
            f"  - Elderly: {pop.get('elderly_estimated', 0):,}\n"
            f"ECONOMIC EXPOSURE: ₹{econ.get('total_damage_crore', 0)} Crore\n"
            f"EVACUATION ESTIMATE: {evac.get('estimated_evac_time_hours', 0)} hours\n"
            f"VEHICLES NEEDED: {evac.get('vehicles_needed', 0)}\n"
            f"AMBULANCES NEEDED: {evac.get('ambulances_needed', 0)}\n"
        )
        
        if spread_data and spread_data.get('is_spreading'):
            brief += (
                f"\nFIRE SPREAD FORECAST:\n"
                f"  Effective Rate: {spread_data.get('effective_spread_rate_kmh', 0)} km/h\n"
                f"  Wind: {spread_data.get('wind_speed_kmh', 0)} km/h\n"
                f"  Spread Risk: {spread_data.get('spread_risk', 'N/A')}\n"
            )
        
        return brief
    
    # ── AI Recommendation ────────────────────────────────────────
    
    def _generate_ai_recommendation(self, event, impact, spread_data):
        """Generate AI-powered recommendation summary."""
        risk = impact.get('composite_risk_score', {}).get('level', 'LOW')
        psych = impact.get('psychological_impact', {}).get('level', 'LOW')
        aqhi = impact.get('air_quality', {}).get('aqi_category', 'GOOD')
        
        if risk == 'CRITICAL':
            urgency = 'IMMEDIATE ACTION REQUIRED'
            recommendation = (
                'This event poses critical risk to human life. Recommend immediate activation of '
                'Emergency Operations Center, deployment of NDRF/SDRF teams, and evacuation of '
                'all populations within the predicted danger zone. Air quality monitoring and '
                'medical teams should be deployed simultaneously.'
            )
        elif risk == 'HIGH':
            urgency = 'URGENT ATTENTION NEEDED'
            recommendation = (
                'This event requires urgent attention. Recommend alerting relevant authorities, '
                'preparing evacuation plans, and deploying air quality monitoring. Community '
                'awareness should be raised through local channels.'
            )
        elif risk == 'MODERATE':
            urgency = 'MONITOR AND PREPARE'
            recommendation = (
                'This event should be actively monitored. Recommend keeping response teams on '
                'standby and issuing informational advisories to the public. Prepare contingency '
                'plans for escalation.'
            )
        else:
            urgency = 'ROUTINE MONITORING'
            recommendation = (
                'This event is currently low risk. Continue routine satellite monitoring. '
                'No immediate action required but maintain awareness for changes.'
            )
        
        return {
            'urgency': urgency,
            'recommendation': recommendation,
            'confidence_note': f"Based on {event.get('confidence', 0)}% AI ensemble confidence",
        }


def generate_advisory(event, impact_data, method_scores, spread_data=None):
    """Convenience function."""
    generator = AIAdvisoryGenerator()
    return generator.generate_advisory(event, impact_data, method_scores, spread_data)


if __name__ == "__main__":
    print("=== AGNI-DRISHTI: AI Advisory Generator Test ===")
    
    mock_event = {
        'lat': 24.5, 'lng': 79.3, 'type': 'Wildfire', 'target_class': 0,
        'confidence': 94.5, 'frp': 85.0,
    }
    mock_impact = {
        'population_exposure': {'total_population': 12500, 'children_estimated': 3500, 'elderly_estimated': 1000},
        'air_quality': {'aqi_category': 'UNHEALTHY', 'health_advisory': 'Avoid outdoor activity.'},
        'psychological_impact': {'level': 'HIGH', 'score': 62},
        'evacuation': {'estimated_evac_time_hours': 4, 'vehicles_needed': 30, 'ambulances_needed': 5},
        'economic_impact': {'total_damage_crore': 45.5},
        'composite_risk_score': {'level': 'HIGH', 'score': 72},
    }
    mock_methods = {'XGBoost': 92, 'CNN': 88, 'RandomForest': 91, 'LightGBM': 90}
    
    advisory = generate_advisory(mock_event, mock_impact, mock_methods)
    print(advisory['situation_report'])
    print("\n--- Public Advisory (English) ---")
    print(advisory['public_advisory_en'])
