"""
ENVIRONMENTAL CONTEXT PROCESSOR - Soil & Environmental Monitoring
Handles soil moisture and environmental conditioning factors

Weight: 20% (Context layer, not alarm trigger)
"""

from typing import Dict, Optional, Tuple
import numpy as np


class EnvironmentalContextProcessor:
    """
    Processes environmental context data into fire susceptibility indicators.
    
    Tertiary detection modality:
    - Slow-changing signals (days/weeks, not seconds)
    - Not an event detector
    - Conditions interpretation of other sensors
    
    Detects:
    1. Soil Dryness - How dry is the environment?
    2. Ignition Susceptibility - How easily would fire spread?
    3. Latent Risk - Underlying danger level even without smoke
    
    Key Philosophy:
    Same chemical reading means different things in different contexts:
    - Wet soil + chemical spike = Probably rotting leaves (IGNORE)
    - Dry soil + chemical spike = Serious fire risk (ALERT)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize environmental processor with thresholds
        
        Args:
            config: Optional configuration dict
        """
        self.config = config or self._default_config()
        
        # Historical tracking for trend analysis
        self.moisture_history = []
        self.max_history_samples = 100
        
        # Drought detection
        self.drought_threshold_days = 7  # 7 days of dry = drought
    
    def _default_config(self) -> Dict:
        """
        Default environmental thresholds
        
        Returns:
            Default config dict
        """
        return {
            # Soil moisture thresholds (percentage)
            'moisture_wet': 60.0,          # Above 60% = wet (safe)
            'moisture_moderate': 40.0,     # 40-60% = moderate
            'moisture_dry': 20.0,          # 20-40% = dry (caution)
            'moisture_critical': 10.0,     # Below 20% = critical (danger)
            
            # Ignition susceptibility factors
            'ignition_wet_multiplier': 0.1,      # Wet soil = very low risk
            'ignition_moderate_multiplier': 0.4, # Moderate = some risk
            'ignition_dry_multiplier': 0.7,      # Dry = high risk
            'ignition_critical_multiplier': 0.95, # Critical = extreme risk
            
            # Temperature modulation (if available)
            'temp_normal': 25.0,           # Normal temperature
            'temp_high': 35.0,             # High temperature increases risk
            'temp_extreme': 45.0,          # Extreme temperature
            
            # Humidity modulation (if available)
            'humidity_normal': 50.0,       # Normal humidity
            'humidity_low': 30.0,          # Low humidity increases risk
            'humidity_critical': 15.0,     # Critical low humidity
        }
    
    def process(self, validated_readings: Dict) -> Dict[str, float]:
        """
        Convert environmental data into fire susceptibility context
        
        Args:
            validated_readings: Dict of Phase-1 validated sensor readings
                Expected keys: 'SOIL_MOISTURE', 'TEMPERATURE', 'HUMIDITY'
                Values: ValidationResult objects from Phase-1
        
        Returns:
            Environmental context dict with normalized scores (0.0-1.0):
            {
                'soil_dryness': float,
                'ignition_susceptibility': float,
                'latent_risk': float,
                'drought_detected': bool,
                'environmental_confidence': float
            }
        """
        context = {}
        
        # Track confidence
        active_sensors = 0
        total_confidence = 0.0
        
        # =====================================================================
        # 1. SOIL DRYNESS - Primary environmental indicator
        # =====================================================================
        if 'SOIL_MOISTURE' in validated_readings:
            moisture_result = validated_readings['SOIL_MOISTURE']
            moisture_percent = moisture_result.value
            
            # Soil dryness is inverse of moisture
            dryness = self._compute_soil_dryness(moisture_percent)
            context['soil_dryness'] = dryness
            
            # Track moisture history
            self._update_moisture_history(moisture_percent)
            
            # Detect drought conditions
            context['drought_detected'] = self._is_drought_condition()
            
            active_sensors += 1
            total_confidence += moisture_result.reliability_score
        else:
            context['soil_dryness'] = 0.5  # Unknown = assume moderate
            context['drought_detected'] = False
        
        # =====================================================================
        # 2. IGNITION SUSCEPTIBILITY - Fire spread likelihood
        # =====================================================================
        ignition_risk = self._compute_ignition_susceptibility(
            validated_readings,
            context.get('soil_dryness', 0.5)
        )
        context['ignition_susceptibility'] = ignition_risk
        
        # =====================================================================
        # 3. LATENT RISK - Underlying danger level
        # =====================================================================
        latent_risk = self._compute_latent_risk(
            context.get('soil_dryness', 0.5),
            context.get('drought_detected', False),
            validated_readings
        )
        context['latent_risk'] = latent_risk
        
        # =====================================================================
        # 4. ENVIRONMENTAL CONFIDENCE
        # =====================================================================
        # Add temperature/humidity to confidence if available
        if 'TEMPERATURE' in validated_readings:
            active_sensors += 1
            total_confidence += validated_readings['TEMPERATURE'].reliability_score
        
        if 'HUMIDITY' in validated_readings:
            active_sensors += 1
            total_confidence += validated_readings['HUMIDITY'].reliability_score
        
        if active_sensors > 0:
            context['environmental_confidence'] = total_confidence / active_sensors
        else:
            context['environmental_confidence'] = 0.0
        
        return context
    
    # =========================================================================
    # SOIL DRYNESS COMPUTATION
    # =========================================================================
    
    def _compute_soil_dryness(self, moisture_percent: float) -> float:
        """
        Convert soil moisture to dryness index
        
        Args:
            moisture_percent: Soil moisture percentage (0-100)
        
        Returns:
            Dryness score: 0.0 (wet) to 1.0 (bone dry)
        """
        # Simple inverse mapping
        dryness = 1.0 - (moisture_percent / 100.0)
        
        # Clamp to valid range
        return max(0.0, min(1.0, dryness))
    
    def _categorize_moisture_level(self, moisture_percent: float) -> str:
        """
        Categorize moisture level
        
        Args:
            moisture_percent: Soil moisture percentage
        
        Returns:
            Category: 'wet', 'moderate', 'dry', or 'critical'
        """
        if moisture_percent >= self.config['moisture_wet']:
            return 'wet'
        elif moisture_percent >= self.config['moisture_moderate']:
            return 'moderate'
        elif moisture_percent >= self.config['moisture_dry']:
            return 'dry'
        else:
            return 'critical'
    
    # =========================================================================
    # IGNITION SUSCEPTIBILITY
    # =========================================================================
    
    def _compute_ignition_susceptibility(
        self, 
        validated_readings: Dict, 
        soil_dryness: float
    ) -> float:
        """
        Compute how easily fire would ignite and spread
        
        Factors:
        - Soil dryness (primary)
        - Temperature (secondary)
        - Humidity (secondary)
        
        Args:
            validated_readings: Validated sensor readings
            soil_dryness: Computed soil dryness (0-1)
        
        Returns:
            Ignition susceptibility: 0.0 (won't burn) to 1.0 (burns like gasoline)
        """
        # Base risk from soil dryness
        base_risk = soil_dryness
        
        # Modulate by temperature (if available)
        temp_multiplier = 1.0
        if 'TEMPERATURE' in validated_readings:
            temp = validated_readings['TEMPERATURE'].value
            temp_multiplier = self._compute_temperature_multiplier(temp)
        
        # Modulate by humidity (if available)
        humidity_multiplier = 1.0
        if 'HUMIDITY' in validated_readings:
            humidity = validated_readings['HUMIDITY'].value
            humidity_multiplier = self._compute_humidity_multiplier(humidity)
        
        # Combined risk
        combined_risk = base_risk * temp_multiplier * humidity_multiplier
        
        # Clamp to valid range
        return max(0.0, min(1.0, combined_risk))
    
    def _compute_temperature_multiplier(self, temperature: float) -> float:
        """
        Compute temperature risk multiplier
        
        High temperature increases ignition risk
        
        Args:
            temperature: Temperature in Celsius
        
        Returns:
            Multiplier: 0.8 (cool) to 1.3 (extreme heat)
        """
        normal = self.config['temp_normal']
        high = self.config['temp_high']
        extreme = self.config['temp_extreme']
        
        if temperature <= normal:
            # Cool weather reduces risk slightly
            return 0.8
        elif temperature <= high:
            # Moderate heat (1.0 = no change)
            ratio = (temperature - normal) / (high - normal)
            return 1.0 + (ratio * 0.15)  # Up to 1.15x
        else:
            # Extreme heat
            ratio = min((temperature - high) / (extreme - high), 1.0)
            return 1.15 + (ratio * 0.15)  # Up to 1.3x
    
    def _compute_humidity_multiplier(self, humidity: float) -> float:
        """
        Compute humidity risk multiplier
        
        Low humidity increases ignition risk
        
        Args:
            humidity: Humidity percentage
        
        Returns:
            Multiplier: 0.8 (humid) to 1.3 (very dry air)
        """
        normal = self.config['humidity_normal']
        low = self.config['humidity_low']
        critical = self.config['humidity_critical']
        
        if humidity >= normal:
            # High humidity reduces risk
            return 0.8
        elif humidity >= low:
            # Moderate humidity
            ratio = (normal - humidity) / (normal - low)
            return 0.8 + (ratio * 0.35)  # 0.8 to 1.15
        else:
            # Very dry air
            ratio = min((low - humidity) / (low - critical), 1.0)
            return 1.15 + (ratio * 0.15)  # Up to 1.3x
    
    # =========================================================================
    # LATENT RISK COMPUTATION
    # =========================================================================
    
    def _compute_latent_risk(
        self,
        soil_dryness: float,
        drought_detected: bool,
        validated_readings: Dict
    ) -> float:
        """
        Compute latent (hidden) fire risk
        
        This is the underlying danger level EVEN WITHOUT smoke/fire
        It's the "readiness to burn" factor
        
        Args:
            soil_dryness: Soil dryness score
            drought_detected: Whether drought conditions exist
            validated_readings: Validated sensor readings
        
        Returns:
            Latent risk: 0.0 (safe) to 1.0 (extreme danger)
        """
        # Base latent risk from soil dryness
        base_latent_risk = soil_dryness ** 1.5  # Exponential - dry is VERY dangerous
        
        # Drought multiplier
        if drought_detected:
            drought_multiplier = 1.3  # 30% increase during drought
        else:
            drought_multiplier = 1.0
        
        # Temperature contribution
        temp_contribution = 0.0
        if 'TEMPERATURE' in validated_readings:
            temp = validated_readings['TEMPERATURE'].value
            if temp > self.config['temp_high']:
                # High temp adds to latent risk
                temp_contribution = 0.2
        
        # Humidity contribution
        humidity_contribution = 0.0
        if 'HUMIDITY' in validated_readings:
            humidity = validated_readings['HUMIDITY'].value
            if humidity < self.config['humidity_low']:
                # Low humidity adds to latent risk
                humidity_contribution = 0.15
        
        # Combined latent risk
        latent_risk = (
            (base_latent_risk * drought_multiplier) +
            temp_contribution +
            humidity_contribution
        )
        
        # Clamp to valid range
        return max(0.0, min(1.0, latent_risk))
    
    # =========================================================================
    # DROUGHT DETECTION
    # =========================================================================
    
    def _update_moisture_history(self, moisture_percent: float):
        """
        Update rolling history of moisture readings
        
        Args:
            moisture_percent: Current moisture reading
        """
        self.moisture_history.append(moisture_percent)
        
        # Keep only last N samples
        if len(self.moisture_history) > self.max_history_samples:
            self.moisture_history.pop(0)
    
    def _is_drought_condition(self) -> bool:
        """
        Detect if drought conditions exist
        
        Drought = sustained low moisture for extended period
        
        Returns:
            True if drought detected, False otherwise
        """
        if len(self.moisture_history) < self.drought_threshold_days:
            return False  # Not enough history
        
        # Check last N days
        recent_samples = self.moisture_history[-self.drought_threshold_days:]
        
        # All samples below dry threshold = drought
        dry_threshold = self.config['moisture_dry']
        all_dry = all(m < dry_threshold for m in recent_samples)
        
        return all_dry
    
    # =========================================================================
    # CONTEXTUAL INTERPRETATION HELPERS
    # =========================================================================
    
    def interpret_chemical_spike(
        self,
        chemical_score: float,
        soil_dryness: float
    ) -> Tuple[str, float]:
        """
        Interpret a chemical spike based on environmental context
        
        Same chemical reading means different things:
        - Wet soil → Probably organic decay
        - Dry soil → Serious fire risk
        
        Args:
            chemical_score: Chemical detection score (0-1)
            soil_dryness: Soil dryness score (0-1)
        
        Returns:
            Tuple of (interpretation, adjusted_score)
        """
        if chemical_score < 0.3:
            return ("No significant chemical detection", chemical_score)
        
        # High chemical + wet soil = organic decay
        if chemical_score > 0.5 and soil_dryness < 0.3:
            adjusted_score = chemical_score * 0.3  # Heavily discount
            return ("Chemical spike in wet conditions - likely organic decay", adjusted_score)
        
        # High chemical + dry soil = fire risk
        if chemical_score > 0.5 and soil_dryness > 0.7:
            adjusted_score = chemical_score * 1.3  # Amplify concern
            return ("Chemical spike in dry conditions - FIRE RISK", adjusted_score)
        
        # Moderate conditions
        return ("Chemical spike in moderate conditions", chemical_score)
    
    def get_fire_weather_index(self, validated_readings: Dict) -> float:
        """
        Compute a simplified Fire Weather Index
        
        Combines multiple environmental factors into single "readiness to burn" score
        
        Args:
            validated_readings: Validated sensor readings
        
        Returns:
            Fire Weather Index: 0.0 (safe) to 1.0 (extreme fire danger)
        """
        factors = []
        
        # Soil moisture
        if 'SOIL_MOISTURE' in validated_readings:
            moisture = validated_readings['SOIL_MOISTURE'].value
            dryness = self._compute_soil_dryness(moisture)
            factors.append(dryness)
        
        # Temperature
        if 'TEMPERATURE' in validated_readings:
            temp = validated_readings['TEMPERATURE'].value
            temp_factor = min((temp - 20) / 30, 1.0)  # 20-50°C range
            temp_factor = max(0.0, temp_factor)
            factors.append(temp_factor)
        
        # Humidity
        if 'HUMIDITY' in validated_readings:
            humidity = validated_readings['HUMIDITY'].value
            humidity_factor = 1.0 - (humidity / 100.0)  # Inverse
            factors.append(humidity_factor)
        
        # Average all factors
        if factors:
            return np.mean(factors)
        else:
            return 0.5  # Unknown = moderate
    
    # =========================================================================
    # CALIBRATION
    # =========================================================================
    
    def calibrate_baseline(self, moisture_readings: list):
        """
        Calibrate baseline from normal environment readings
        
        Args:
            moisture_readings: List of soil moisture readings from normal conditions
        """
        if not moisture_readings:
            return
        
        # Set baselines
        avg_moisture = np.median(moisture_readings)
        
        # Adjust thresholds relative to local baseline
        print(f"✅ Environmental baselines calibrated:")
        print(f"   Average moisture: {avg_moisture:.1f}%")
        print(f"   Dry threshold: {self.config['moisture_dry']:.1f}%")
        print(f"   Critical threshold: {self.config['moisture_critical']:.1f}%")
    
    def get_statistics(self) -> Dict:
        """
        Get processor statistics
        
        Returns:
            Dict with processing stats
        """
        return {
            'moisture_history_samples': len(self.moisture_history),
            'current_moisture_avg': np.mean(self.moisture_history) if self.moisture_history else None,
            'drought_detected': self._is_drought_condition(),
            'config': self.config
        }