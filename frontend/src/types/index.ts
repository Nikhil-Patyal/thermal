export interface MethodScores {
  [key: string]: number;
}

export interface SpreadPrediction {
  radius_km: number;
  area_sq_km: number;
  confidence: number;
}

export interface SpreadData {
  is_spreading: boolean;
  wind_speed_kmh: number;
  wind_direction_deg: number;
  vegetation_type: string;
  spread_rate_kmh: number;
  spread_risk: string;
  predictions: { [key: string]: SpreadPrediction };
}

export interface VulnerableFacility {
  type: string;
  icon: string;
  priority: string;
  distance_km: number;
  estimated_occupants: number;
  status: string;
}

export interface ToxicGas {
  level: number;
  unit: string;
  risk: string;
}

export interface ImpactData {
  total_population: number;
  children_at_risk: number;
  elderly_at_risk: number;
  zone_type: string;
  danger_area_sq_km: number;
  aqi_category: string;
  aqi_color: string;
  peak_pm25: number;
  health_advisory: string;
  mask_recommended: boolean;
  toxic_gases: { [key: string]: ToxicGas };
  psych_score: number;
  psych_level: string;
  psych_description: string;
  psych_factors: { [key: string]: number };
  ptsd_risk_pct: number;
  counseling_teams_needed: number;
  vulnerable_facilities: VulnerableFacility[];
  critical_facilities_count: number;
  evac_time_hours: number;
  evac_directions: { direction: string; angle: number; safety_rating: number }[];
  evac_avoid: string;
  vehicles_needed: number;
  economic_damage_crore: number;
  economic_breakdown: { [key: string]: string };
  water_risk: string;
  water_advisory: string;
  composite_risk_score: number;
  composite_risk_level: string;
  risk_breakdown: { [key: string]: number };
}

export interface ActionItem {
  priority: string;
  action: string;
  responsible: string;
}

export interface AdvisoryData {
  situation_report: string;
  action_items: ActionItem[];
  public_advisory_en: string;
  public_advisory_hi: string;
  sms_alert: string;
  ai_recommendation: { urgency: string; recommendation: string; confidence_note: string };
  psych_guidance_responders: string[];
  psych_guidance_families: string[];
  psych_helplines: { name: string; number: string }[];
}

export interface SpectralData {
  nbr: number;
  ndvi: number;
  swir_anomaly: number;
  mir_tir_ratio: number;
  est_temperature: number;
}

export interface ThermalEvent {
  id: string;
  lat: number;
  lng: number;
  type: string;
  color: string;
  confidence: number;
  method_scores: MethodScores;
  frp: number;
  persistence_days: number;
  detection_age_days: number;
  dist_to_forest: number;
  dist_to_industry: number;
  dist_to_cropland: number;
  risk_score: string;
  composite_risk: number;
  toxic_radius_km: number;
  lives_impacted: number;
  impact: ImpactData;
  spread: SpreadData;
  advisory: AdvisoryData;
  spectral: SpectralData;
}

export interface Metadata {
  total_events: number;
  by_type: { [key: string]: number };
  by_risk: { [key: string]: number };
  total_population_protected: number;
  total_economic_exposure_crore: number;
  avg_confidence: number;
  method_performance: { [key: string]: number };
  spreading_events: number;
  critical_events: number;
}
