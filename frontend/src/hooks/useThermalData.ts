import { useState, useEffect, useMemo } from 'react';

// ── Backend Hotspot type (matches Django serializer) ──────────────
export interface BackendHotspot {
  id: number;
  frp: number | null;
  scan: number | null;
  confidence: number | null;
  brightness: number | null;
  acquisition_date: string | null;
  lat: number;
  lng: number;
  predicted_class: string | null;
  confidence_score: number | null;
  fetched_at: string | null;
  economic_exposure: { id: number; gdp: number; industrial_output: number | null } | null;
  air_quality: { id: number; pm25: number | null; no2: number | null; aqi: number | null } | null;
  safe_route: { id: number; distance_km: number; travel_time_min: number } | null;
  weather: { id: number; temperature_c: number | null; wind_speed_ms: number | null; humidity: number | null } | null;
  population_exposure: { id: number; population_count: number } | null;
  water_quality: unknown | null;
  shap_values: Record<string, number> | null;
}

const BACKEND = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export function useThermalData() {
  const [hotspots, setHotspots] = useState<BackendHotspot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [typeFilter, setTypeFilter] = useState('All Types');
  const [riskFilter, setRiskFilter] = useState('All Risks');
  const [timeFilter, setTimeFilter] = useState('All Time');

  // ── Fetch real hotspot list from backend ─────────────────────────
  useEffect(() => {
    setLoading(true);
    fetch(`${BACKEND}/api/hotspots/?limit=500`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: BackendHotspot[]) => {
        setHotspots(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('useThermalData: failed to fetch hotspots', err);
        setError(String(err));
        setLoading(false);
      });
  }, []);

  // ── Filtering ─────────────────────────────────────────────────────
  const filteredHotspots = useMemo(() => {
    let result = hotspots;
    if (typeFilter !== 'All Types') {
      result = result.filter((h) => h.predicted_class === typeFilter);
    }
    if (riskFilter !== 'All Risks') {
      // High = FRP > 500, Medium = 50-500, Low = <50
      result = result.filter((h) => {
        const frp = h.frp ?? 0;
        if (riskFilter === 'HIGH') return frp > 500;
        if (riskFilter === 'MEDIUM') return frp >= 50 && frp <= 500;
        if (riskFilter === 'LOW') return frp < 50;
        return true;
      });
    }
    return result;
  }, [hotspots, typeFilter, riskFilter, timeFilter]);

  // ── Computed Stats ────────────────────────────────────────────────
  const criticalCount = useMemo(
    () => hotspots.filter((h) => (h.frp ?? 0) > 500).length,
    [hotspots]
  );
  const totalPopulationExposed = useMemo(
    () => hotspots.reduce((a, h) => a + (h.population_exposure?.population_count ?? 0), 0),
    [hotspots]
  );
  const avgConfidence = useMemo(() => {
    const scored = hotspots.filter((h) => h.confidence_score != null);
    if (!scored.length) return 0;
    return scored.reduce((a, h) => a + (h.confidence_score ?? 0), 0) / scored.length;
  }, [hotspots]);

  // Unique predicted classes for filter dropdown
  const classTypes = useMemo(() => {
    const set = new Set(hotspots.map((h) => h.predicted_class).filter(Boolean) as string[]);
    return Array.from(set).sort();
  }, [hotspots]);

  return {
    hotspots,
    filteredHotspots,
    loading,
    error,
    typeFilter,
    setTypeFilter,
    riskFilter,
    setRiskFilter,
    timeFilter,
    setTimeFilter,
    criticalCount,
    totalPopulationExposed,
    avgConfidence,
    classTypes,
  };
}
