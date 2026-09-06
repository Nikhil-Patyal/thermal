"""
AGNI-DRISHTI: Multi-Spectral Band Analyzer
===========================================
Simulates and analyzes multi-spectral band ratios from satellite sensors
(SWIR, TIR, MIR) to distinguish combustion types:
  - Band ratio features separate high-temp combustion (industrial) from biomass burning
  - Normalized Burn Ratio (NBR) for vegetation fire confirmation
  - SWIR anomaly index for gas flare identification
"""

import numpy as np
import warnings
warnings.filterwarnings('ignore')


# ── Spectral Band Constants ──────────────────────────────────────
# Simulated center wavelengths (μm)
BANDS = {
    'SWIR_1': 1.6,   # Short-Wave Infrared Band 1
    'SWIR_2': 2.2,   # Short-Wave Infrared Band 2
    'TIR_1': 10.8,   # Thermal Infrared Band 1
    'TIR_2': 12.0,   # Thermal Infrared Band 2
    'MIR': 3.9,      # Mid-Infrared
    'NIR': 0.86,     # Near-Infrared
    'RED': 0.66,     # Visible Red
    'GREEN': 0.55,   # Visible Green
}


def generate_spectral_signatures(n_samples, target_class):
    """
    Generate realistic multi-spectral signatures for each fire type.
    Based on Planck radiation curves and known spectral characteristics.
    """
    sigs = {}
    
    if target_class == 0:  # Wildfire
        # Biomass combustion: ~800-1200K, strong MIR, moderate SWIR, high TIR
        sigs['MIR'] = np.random.normal(340, 8, n_samples)
        sigs['SWIR_1'] = np.random.normal(1.2, 0.3, n_samples)
        sigs['SWIR_2'] = np.random.normal(2.5, 0.6, n_samples)
        sigs['TIR_1'] = np.random.normal(310, 6, n_samples)
        sigs['TIR_2'] = np.random.normal(295, 5, n_samples)
        sigs['NIR'] = np.random.normal(0.15, 0.05, n_samples)  # Low (burned vegetation)
        sigs['RED'] = np.random.normal(0.08, 0.03, n_samples)
        sigs['GREEN'] = np.random.normal(0.06, 0.02, n_samples)
        
    elif target_class == 1:  # Industrial Fire
        # High-temperature combustion: ~1500-2000K, very strong SWIR
        sigs['MIR'] = np.random.normal(380, 12, n_samples)
        sigs['SWIR_1'] = np.random.normal(4.5, 1.0, n_samples)
        sigs['SWIR_2'] = np.random.normal(6.0, 1.5, n_samples)
        sigs['TIR_1'] = np.random.normal(330, 8, n_samples)
        sigs['TIR_2'] = np.random.normal(310, 7, n_samples)
        sigs['NIR'] = np.random.normal(0.25, 0.08, n_samples)
        sigs['RED'] = np.random.normal(0.20, 0.06, n_samples)
        sigs['GREEN'] = np.random.normal(0.18, 0.05, n_samples)
        
    elif target_class == 2:  # Gas Flare
        # Very high temperature: ~2000-2500K, extreme SWIR, moderate area
        sigs['MIR'] = np.random.normal(400, 15, n_samples)
        sigs['SWIR_1'] = np.random.normal(8.0, 2.0, n_samples)
        sigs['SWIR_2'] = np.random.normal(10.0, 2.5, n_samples)
        sigs['TIR_1'] = np.random.normal(320, 5, n_samples)
        sigs['TIR_2'] = np.random.normal(305, 4, n_samples)
        sigs['NIR'] = np.random.normal(0.30, 0.10, n_samples)
        sigs['RED'] = np.random.normal(0.25, 0.08, n_samples)
        sigs['GREEN'] = np.random.normal(0.22, 0.07, n_samples)
        
    elif target_class == 3:  # Agriculture Burning
        # Low-temperature smoldering: ~600-900K, moderate MIR, lower SWIR
        sigs['MIR'] = np.random.normal(325, 10, n_samples)
        sigs['SWIR_1'] = np.random.normal(0.8, 0.2, n_samples)
        sigs['SWIR_2'] = np.random.normal(1.5, 0.4, n_samples)
        sigs['TIR_1'] = np.random.normal(305, 7, n_samples)
        sigs['TIR_2'] = np.random.normal(290, 6, n_samples)
        sigs['NIR'] = np.random.normal(0.20, 0.06, n_samples)
        sigs['RED'] = np.random.normal(0.12, 0.04, n_samples)
        sigs['GREEN'] = np.random.normal(0.10, 0.03, n_samples)
        
    else:  # Mining Activity (class 4)
        # Moderate sustained heat: ~500-800K, moderate all bands
        sigs['MIR'] = np.random.normal(315, 8, n_samples)
        sigs['SWIR_1'] = np.random.normal(0.6, 0.2, n_samples)
        sigs['SWIR_2'] = np.random.normal(1.0, 0.3, n_samples)
        sigs['TIR_1'] = np.random.normal(300, 6, n_samples)
        sigs['TIR_2'] = np.random.normal(288, 5, n_samples)
        sigs['NIR'] = np.random.normal(0.18, 0.05, n_samples)
        sigs['RED'] = np.random.normal(0.10, 0.03, n_samples)
        sigs['GREEN'] = np.random.normal(0.08, 0.02, n_samples)
    
    return sigs


def compute_spectral_indices(sigs):
    """
    Compute derived spectral indices that are discriminative for fire classification.
    """
    features = {}
    
    # 1. Normalized Burn Ratio (NBR) — high for active vegetation fires
    features['nbr'] = (sigs['NIR'] - sigs['SWIR_2']) / (sigs['NIR'] + sigs['SWIR_2'] + 1e-8)
    
    # 2. SWIR Anomaly Index — high for gas flares and industrial
    features['swir_anomaly'] = sigs['SWIR_2'] / (sigs['SWIR_1'] + 1e-8)
    
    # 3. TIR Split Window Difference — combustion temperature indicator
    features['tir_split'] = sigs['TIR_1'] - sigs['TIR_2']
    
    # 4. MIR/TIR Ratio — separates high-temp from low-temp sources
    features['mir_tir_ratio'] = sigs['MIR'] / (sigs['TIR_1'] + 1e-8)
    
    # 5. SWIR/MIR Ratio — gas flare vs biomass fire discriminator
    features['swir_mir_ratio'] = sigs['SWIR_2'] / (sigs['MIR'] + 1e-8)
    
    # 6. Normalized Difference Vegetation Index (NDVI) — context
    features['ndvi'] = (sigs['NIR'] - sigs['RED']) / (sigs['NIR'] + sigs['RED'] + 1e-8)
    
    # 7. Enhanced Vegetation Index (EVI) — better saturation handling
    features['evi'] = 2.5 * (sigs['NIR'] - sigs['RED']) / (sigs['NIR'] + 6 * sigs['RED'] - 7.5 * sigs['GREEN'] + 1 + 1e-8)
    
    # 8. Fire Temperature Estimate (Stefan-Boltzmann approximation)
    features['est_temperature'] = (sigs['MIR'] / 5.67e-8) ** 0.25
    
    # 9. Combustion Efficiency Index
    features['combustion_efficiency'] = sigs['SWIR_2'] / (sigs['MIR'] - sigs['TIR_1'] + 1e-8)
    
    # 10. SWIR Saturation Flag (binary)
    features['swir_saturated'] = (sigs['SWIR_2'] > 5.0).astype(float)
    
    # 11. Band Ratio Complex — multi-band signature
    features['band_ratio_complex'] = (sigs['MIR'] * sigs['SWIR_2']) / (sigs['TIR_1'] * sigs['NIR'] + 1e-8)
    
    # 12. Thermal Anomaly Magnitude
    features['thermal_anomaly_mag'] = sigs['MIR'] - 0.5 * (sigs['TIR_1'] + sigs['TIR_2'])
    
    return features


def generate_spectral_features_for_dataset(targets, n_samples):
    """
    Generate a complete spectral feature matrix for a dataset with given target labels.
    Returns dict of feature arrays.
    """
    all_features = {}
    
    for cls in range(5):
        mask = targets == cls
        n_cls = int(np.sum(mask))
        if n_cls == 0:
            continue
        
        sigs = generate_spectral_signatures(n_cls, cls)
        indices = compute_spectral_indices(sigs)
        
        for key, values in indices.items():
            if key not in all_features:
                all_features[key] = np.zeros(n_samples)
            all_features[key][mask] = values
    
    return all_features


def get_spectral_feature_names():
    """Return list of spectral feature column names."""
    return [
        'nbr', 'swir_anomaly', 'tir_split', 'mir_tir_ratio', 'swir_mir_ratio',
        'ndvi', 'evi', 'est_temperature', 'combustion_efficiency', 'swir_saturated',
        'band_ratio_complex', 'thermal_anomaly_mag'
    ]


def compute_spectral_for_single_event(target_class):
    """Compute spectral features for a single event (for inference/display)."""
    sigs = generate_spectral_signatures(1, target_class)
    indices = compute_spectral_indices(sigs)
    return {k: float(v[0]) for k, v in indices.items()}


if __name__ == "__main__":
    print("=== AGNI-DRISHTI: Spectral Band Analyzer Test ===")
    np.random.seed(42)
    
    targets = np.random.choice([0, 1, 2, 3, 4], size=100, p=[0.4, 0.15, 0.1, 0.25, 0.1])
    features = generate_spectral_features_for_dataset(targets, 100)
    
    print(f"Generated {len(features)} spectral features for {len(targets)} samples")
    for name, values in features.items():
        print(f"  {name}: mean={np.mean(values):.4f}, std={np.std(values):.4f}")
