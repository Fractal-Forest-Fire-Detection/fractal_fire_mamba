"""
CHEMICAL PROCESSOR - Gas Sensor Analysis
Handles BME688 / gas sensor data for fire detection

Weight: 50% (Primary early-warning system)
"""

from typing import Dict, Optional
import numpy as np


class ChemicalProcessor:
    """
    Processes chemical/gas sensor data into semantic fire indicators.
    
    Primary detection modality:
    - Chemical signatures appear BEFORE visible smoke
    - Works in darkness, fog, occlusion
    - Hard to spoof accidentally
    - Highest semantic value
    
    Detects:
    1. VOCs (Volatile Organic Compounds) - General air chemistry changes
    2. Terpenes - Heat-stressed plant emissions (PRE-COMBUSTION warning)
    3. Combustion Byproducts - Active fire gases (CO, smoke particles)
    4. Organic Emissions - Baseline environmental monitoring
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize chemical processor with calibration parameters
        
        Args:
            config: Optional configuration dict with calibration values
        """
        self.config = config or self._default_config()
        
        # Historical baseline (for detecting rapid changes)
        self.voc_baseline_history = []
        self.max_baseline_samples = 100
        
        # Rapid change detector
        self.last_voc_value = None
        self.voc_spike_threshold = 2.0  # 2x increase = spike
    
    def _default_config(self) -> Dict:
        """
        Default calibration parameters for gas sensors
        
        These should be calibrated based on your specific:
        - BME688 sensor baseline
        - Forest environment
        - Altitude/climate
        
        Returns:
            Default config dict
        """
        return {
            # VOC thresholds (PPM - parts per million)
            'voc_normal_baseline': 100,      # Normal forest air
            'voc_elevated_threshold': 300,   # Elevated concern
            'voc_danger_threshold': 500,     # High danger
            
            # Terpene thresholds (PPM)
            'terpene_normal': 50,            # Normal plant emissions
            'terpene_stress_threshold': 150, # Heat stress detected
            'terpene_danger_threshold': 300, # Extreme stress (pre-fire)
            
            # Combustion byproduct thresholds (PPM)
            'co_normal': 10,                 # Normal CO levels
            'co_combustion_threshold': 50,   # Active combustion
            'co_danger_threshold': 100,      # High danger
            
            # Smoke particle density (if available from MQ-2/MQ-135)
            'smoke_normal': 50,
            'smoke_threshold': 200,
            'smoke_danger': 400,
            
            # Organic emissions baseline shift
            'organic_baseline': 80,
            'organic_shift_threshold': 150,
        }
    
    def process(self, validated_readings: Dict) -> Dict[str, float]:
        """
        Convert raw gas readings into chemical state features
        
        Args:
            validated_readings: Dict of Phase-1 validated sensor readings
                Expected keys: 'VOC', 'TERPENE', 'CO', 'SMOKE', etc.
                Values: ValidationResult objects from Phase-1
        
        Returns:
            Chemical state dict with normalized scores (0.0-1.0):
            {
                'voc_level': float,
                'terpene_level': float,
                'combustion_byproducts': float,
                'organic_emissions': float,
                'rapid_change_detected': bool,
                'chemical_confidence': float
            }
        """
        chemical_state = {}
        
        # Track how many sensors contributed (for confidence calculation)
        active_sensors = 0
        total_confidence = 0.0
        
        # =====================================================================
        # 1. VOC LEVEL - General air chemistry
        # =====================================================================
        if 'VOC' in validated_readings:
            voc_result = validated_readings['VOC']
            voc_level = self._normalize_voc(voc_result.value)
            chemical_state['voc_level'] = voc_level
            
            # Track baseline
            self._update_voc_baseline(voc_result.value)
            
            # Detect rapid spikes
            if self._is_rapid_voc_spike(voc_result.value):
                chemical_state['rapid_change_detected'] = True
            
            active_sensors += 1
            total_confidence += voc_result.reliability_score
        else:
            chemical_state['voc_level'] = 0.0
        
        # =====================================================================
        # 2. TERPENE LEVEL - Pre-combustion warning
        # =====================================================================
        if 'TERPENE' in validated_readings:
            terpene_result = validated_readings['TERPENE']
            terpene_level = self._normalize_terpene(terpene_result.value)
            chemical_state['terpene_level'] = terpene_level
            
            active_sensors += 1
            total_confidence += terpene_result.reliability_score
        else:
            chemical_state['terpene_level'] = 0.0
        
        # =====================================================================
        # 3. COMBUSTION BYPRODUCTS - Active fire
        # =====================================================================
        combustion_score = self._detect_combustion(validated_readings)
        chemical_state['combustion_byproducts'] = combustion_score
        
        # Add to confidence if combustion sensors were available
        if 'CO' in validated_readings or 'SMOKE' in validated_readings:
            if 'CO' in validated_readings:
                active_sensors += 1
                total_confidence += validated_readings['CO'].reliability_score
            if 'SMOKE' in validated_readings:
                active_sensors += 1
                total_confidence += validated_readings['SMOKE'].reliability_score
        
        # =====================================================================
        # 4. ORGANIC EMISSIONS - Baseline monitoring
        # =====================================================================
        organic_level = self._compute_organic_baseline_shift(validated_readings)
        chemical_state['organic_emissions'] = organic_level
        
        # =====================================================================
        # 5. RAPID CHANGE FLAG
        # =====================================================================
        if 'rapid_change_detected' not in chemical_state:
            chemical_state['rapid_change_detected'] = False
        
        # =====================================================================
        # 6. CHEMICAL CONFIDENCE - How much can we trust this reading?
        # =====================================================================
        if active_sensors > 0:
            chemical_state['chemical_confidence'] = total_confidence / active_sensors
        else:
            chemical_state['chemical_confidence'] = 0.0
        
        return chemical_state
    
    # =========================================================================
    # NORMALIZATION FUNCTIONS - Convert raw values to 0-1 scale
    # =========================================================================
    
    def _normalize_voc(self, raw_value: float) -> float:
        """
        Normalize VOC reading to 0-1 danger scale
        
        Args:
            raw_value: Raw VOC reading in PPM
        
        Returns:
            Normalized score: 0.0 (safe) to 1.0 (danger)
        """
        baseline = self.config['voc_normal_baseline']
        danger = self.config['voc_danger_threshold']
        
        # Clamp to valid range
        if raw_value <= baseline:
            return 0.0
        elif raw_value >= danger:
            return 1.0
        else:
            # Linear interpolation between baseline and danger
            normalized = (raw_value - baseline) / (danger - baseline)
            return min(max(normalized, 0.0), 1.0)
    
    def _normalize_terpene(self, raw_value: float) -> float:
        """
        Normalize terpene level to 0-1 stress scale
        
        High terpenes = heat-stressed plants = PRE-COMBUSTION warning
        
        Args:
            raw_value: Raw terpene reading in PPM
        
        Returns:
            Normalized score: 0.0 (normal) to 1.0 (extreme stress)
        """
        normal = self.config['terpene_normal']
        danger = self.config['terpene_danger_threshold']
        
        if raw_value <= normal:
            return 0.0
        elif raw_value >= danger:
            return 1.0
        else:
            normalized = (raw_value - normal) / (danger - normal)
            return min(max(normalized, 0.0), 1.0)
    
    def _normalize_co(self, raw_value: float) -> float:
        """
        Normalize CO (carbon monoxide) to 0-1 combustion scale
        
        Args:
            raw_value: Raw CO reading in PPM
        
        Returns:
            Normalized score: 0.0 (safe) to 1.0 (active combustion)
        """
        normal = self.config['co_normal']
        danger = self.config['co_danger_threshold']
        
        if raw_value <= normal:
            return 0.0
        elif raw_value >= danger:
            return 1.0
        else:
            normalized = (raw_value - normal) / (danger - normal)
            return min(max(normalized, 0.0), 1.0)
    
    def _normalize_smoke(self, raw_value: float) -> float:
        """
        Normalize smoke particle density to 0-1 scale
        
        Args:
            raw_value: Raw smoke sensor reading (MQ-2/MQ-135)
        
        Returns:
            Normalized score: 0.0 (clear) to 1.0 (heavy smoke)
        """
        normal = self.config['smoke_normal']
        danger = self.config['smoke_danger']
        
        if raw_value <= normal:
            return 0.0
        elif raw_value >= danger:
            return 1.0
        else:
            normalized = (raw_value - normal) / (danger - normal)
            return min(max(normalized, 0.0), 1.0)
    
    # =========================================================================
    # DETECTION FUNCTIONS
    # =========================================================================
    
    def _detect_combustion(self, validated_readings: Dict) -> float:
        """
        Detect combustion byproducts (CO + smoke)
        
        Combines multiple gas sensors to detect active fire
        
        Args:
            validated_readings: Dict of validated sensor readings
        
        Returns:
            Combustion score: 0.0 (no combustion) to 1.0 (active fire)
        """
        combustion_indicators = []
        
        # Check CO sensor
        if 'CO' in validated_readings:
            co_value = validated_readings['CO'].value
            co_score = self._normalize_co(co_value)
            combustion_indicators.append(co_score)
        
        # Check smoke sensor
        if 'SMOKE' in validated_readings:
            smoke_value = validated_readings['SMOKE'].value
            smoke_score = self._normalize_smoke(smoke_value)
            combustion_indicators.append(smoke_score)
        
        # Average all combustion indicators
        if combustion_indicators:
            return np.mean(combustion_indicators)
        else:
            return 0.0
    
    def _compute_organic_baseline_shift(self, validated_readings: Dict) -> float:
        """
        Compute shift from normal organic emissions baseline
        
        This is a general "something changed" detector
        
        Args:
            validated_readings: Dict of validated sensor readings
        
        Returns:
            Baseline shift score: 0.0 (normal) to 1.0 (major shift)
        """
        # Use VOC as proxy for organic emissions if available
        if 'VOC' in validated_readings:
            voc_value = validated_readings['VOC'].value
            baseline = self.config['organic_baseline']
            threshold = self.config['organic_shift_threshold']
            
            if voc_value <= baseline:
                return 0.0
            elif voc_value >= threshold:
                return 1.0
            else:
                return (voc_value - baseline) / (threshold - baseline)
        
        return 0.0
    
    # =========================================================================
    # RAPID CHANGE DETECTION
    # =========================================================================
    
    def _update_voc_baseline(self, current_voc: float):
        """
        Update rolling baseline of VOC readings
        
        Used to detect sudden spikes
        
        Args:
            current_voc: Current VOC reading
        """
        self.voc_baseline_history.append(current_voc)
        
        # Keep only last N samples
        if len(self.voc_baseline_history) > self.max_baseline_samples:
            self.voc_baseline_history.pop(0)
    
    def _is_rapid_voc_spike(self, current_voc: float) -> bool:
        """
        Detect if VOC spiked suddenly (2x increase)
        
        Rapid changes are extremely suspicious
        
        Args:
            current_voc: Current VOC reading
        
        Returns:
            True if spike detected, False otherwise
        """
        if self.last_voc_value is None:
            self.last_voc_value = current_voc
            return False
        
        # Check if current value is 2x the previous
        if current_voc > self.last_voc_value * self.voc_spike_threshold:
            spike_detected = True
        else:
            spike_detected = False
        
        self.last_voc_value = current_voc
        return spike_detected
    
    # =========================================================================
    # CALIBRATION HELPERS
    # =========================================================================
    
    def calibrate_baseline(self, readings: list, sensor_type: str):
        """
        Calibrate baseline from clean environment readings
        
        Use this during installation to set site-specific baselines
        
        Args:
            readings: List of sensor readings from clean environment
            sensor_type: 'voc', 'terpene', 'co', or 'smoke'
        """
        if not readings:
            return
        
        baseline = np.median(readings)  # Use median to ignore outliers
        
        if sensor_type == 'voc':
            self.config['voc_normal_baseline'] = baseline
            print(f"✅ VOC baseline calibrated to {baseline:.1f} PPM")
        
        elif sensor_type == 'terpene':
            self.config['terpene_normal'] = baseline
            print(f"✅ Terpene baseline calibrated to {baseline:.1f} PPM")
        
        elif sensor_type == 'co':
            self.config['co_normal'] = baseline
            print(f"✅ CO baseline calibrated to {baseline:.1f} PPM")
        
        elif sensor_type == 'smoke':
            self.config['smoke_normal'] = baseline
            print(f"✅ Smoke baseline calibrated to {baseline:.1f}")
    
    def get_statistics(self) -> Dict:
        """
        Get processor statistics
        
        Returns:
            Dict with processing stats
        """
        return {
            'voc_baseline_samples': len(self.voc_baseline_history),
            'current_voc_baseline': np.median(self.voc_baseline_history) if self.voc_baseline_history else None,
            'config': self.config
        }
